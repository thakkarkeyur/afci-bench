import { createOrderUseCase, CreateOrderPorts } from './index';
import { OrderRequest } from '@afci-bench/contracts';
import { Order, OrderRepository } from '@afci-bench/core';
import { Logger, LogOutput, RequestLogEntry, ErrorLogEntry } from '@afci-bench/observability';

class MockLogOutput implements LogOutput {
  public logs: Array<{ level: string; entry: RequestLogEntry | ErrorLogEntry }> = [];

  write(level: string, entry: RequestLogEntry | ErrorLogEntry): void {
    this.logs.push({ level, entry });
  }
}

function createMockRepository(savedOrder?: Order): OrderRepository {
  return {
    save: jest.fn().mockResolvedValue(savedOrder),
    findById: jest.fn().mockResolvedValue(null),
    findByCustomerId: jest.fn().mockResolvedValue([]),
    findAll: jest.fn().mockResolvedValue({ data: [], total: 0 }),
    update: jest.fn().mockResolvedValue(null),
  };
}

describe('createOrderUseCase', () => {
  let mockLogOutput: MockLogOutput;
  let logger: Logger;
  const correlationId = 'test-correlation-id';

  beforeEach(() => {
    mockLogOutput = new MockLogOutput();
    logger = new Logger(mockLogOutput);
  });

  it('should create order successfully with valid input', async () => {
    const input: OrderRequest = {
      customerId: 'cust-123',
      items: [
        { productId: 'prod-1', name: 'Widget', quantity: 2, unitPrice: 10.5 },
        { productId: 'prod-2', name: 'Gadget', quantity: 1, unitPrice: 25 },
      ],
    };

    const mockRepo = createMockRepository();
    (mockRepo.save as jest.Mock).mockImplementation((order: Order) =>
      Promise.resolve(order)
    );

    const ports: CreateOrderPorts = {
      orderRepository: mockRepo,
      logger,
      correlationId,
    };

    const result = await createOrderUseCase(input, ports);

    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data?.customerId).toBe('cust-123');
    expect(result.data?.items).toHaveLength(2);
    expect(result.data?.total).toBe(46); // 2*10.5 + 1*25 = 21 + 25 = 46
    expect(result.data?.status).toBe('pending');
    expect(mockRepo.save).toHaveBeenCalledTimes(1);

    // Verify logging
    const successLog = mockLogOutput.logs.find(
      (l) => (l.entry as RequestLogEntry).status === 'success'
    );
    expect(successLog).toBeDefined();
    expect((successLog?.entry as RequestLogEntry).correlationId).toBe(correlationId);
    expect((successLog?.entry as RequestLogEntry).operation).toBe('createOrder');
  });

  it('should return validation errors for invalid input', async () => {
    const input: OrderRequest = {
      customerId: '',
      items: [],
    };

    const mockRepo = createMockRepository();
    const ports: CreateOrderPorts = {
      orderRepository: mockRepo,
      logger,
      correlationId,
    };

    const result = await createOrderUseCase(input, ports);

    expect(result.success).toBe(false);
    expect(result.errors).toBeDefined();
    expect(result.errors).toContain('customerId is required');
    expect(result.errors).toContain('Order must have at least one item');
    expect(mockRepo.save).not.toHaveBeenCalled();

    // Verify fail log
    const failLog = mockLogOutput.logs.find(
      (l) => (l.entry as RequestLogEntry).status === 'fail'
    );
    expect(failLog).toBeDefined();
  });

  it('should handle repository errors gracefully', async () => {
    const input: OrderRequest = {
      customerId: 'cust-123',
      items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
    };

    const mockRepo = createMockRepository();
    (mockRepo.save as jest.Mock).mockRejectedValue(new Error('Database connection failed'));

    const ports: CreateOrderPorts = {
      orderRepository: mockRepo,
      logger,
      correlationId,
    };

    const result = await createOrderUseCase(input, ports);

    expect(result.success).toBe(false);
    expect(result.errors).toContain('Database connection failed');

    // Verify error log
    const errorLog = mockLogOutput.logs.find(
      (l) => (l.entry as ErrorLogEntry).errorType === 'CreateOrderError'
    );
    expect(errorLog).toBeDefined();
    expect((errorLog?.entry as ErrorLogEntry).message).toBe('Database connection failed');
  });

  it('should calculate item subtotals correctly', async () => {
    const input: OrderRequest = {
      customerId: 'cust-123',
      items: [
        { productId: 'prod-1', name: 'Widget', quantity: 3, unitPrice: 15.33 },
      ],
    };

    const mockRepo = createMockRepository();
    (mockRepo.save as jest.Mock).mockImplementation((order: Order) =>
      Promise.resolve(order)
    );

    const ports: CreateOrderPorts = {
      orderRepository: mockRepo,
      logger,
      correlationId,
    };

    const result = await createOrderUseCase(input, ports);

    expect(result.success).toBe(true);
    expect(result.data?.items[0].subtotal).toBe(45.99); // 3 * 15.33 = 45.99
    expect(result.data?.total).toBe(45.99);
  });

  it('should include correlationId in all logs', async () => {
    const input: OrderRequest = {
      customerId: 'cust-123',
      items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
    };

    const mockRepo = createMockRepository();
    (mockRepo.save as jest.Mock).mockImplementation((order: Order) =>
      Promise.resolve(order)
    );

    const ports: CreateOrderPorts = {
      orderRepository: mockRepo,
      logger,
      correlationId: 'my-unique-correlation-id',
    };

    await createOrderUseCase(input, ports);

    expect(mockLogOutput.logs.length).toBeGreaterThan(0);
    mockLogOutput.logs.forEach((log) => {
      expect(log.entry.correlationId).toBe('my-unique-correlation-id');
    });
  });
});
