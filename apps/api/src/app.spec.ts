import request from 'supertest';
import { createApp } from './app';
import { OrderRequest, OrderResponse, ErrorResponse } from '@afci-bench/contracts';
import { LogOutput, RequestLogEntry, ErrorLogEntry } from '@afci-bench/observability';
import { resetOrderRepository } from '@afci-bench/infra';

class TestLogOutput implements LogOutput {
  public logs: Array<{ level: string; entry: RequestLogEntry | ErrorLogEntry }> = [];

  write(level: string, entry: RequestLogEntry | ErrorLogEntry): void {
    this.logs.push({ level, entry });
  }

  clear(): void {
    this.logs = [];
  }

  getRequestLogs(): RequestLogEntry[] {
    return this.logs
      .filter((l) => 'operation' in l.entry)
      .map((l) => l.entry as RequestLogEntry);
  }

  getErrorLogs(): ErrorLogEntry[] {
    return this.logs
      .filter((l) => 'errorType' in l.entry)
      .map((l) => l.entry as ErrorLogEntry);
  }
}

describe('API Integration Tests', () => {
  let testLogOutput: TestLogOutput;

  beforeEach(() => {
    testLogOutput = new TestLogOutput();
    resetOrderRepository();
  });

  describe('GET /health', () => {
    it('should return health status', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const response = await request(app).get('/health');

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('ok');
      expect(response.body.timestamp).toBeDefined();
    });

    it('should log required fields and propagate correlationId', async () => {
      const app = createApp({ logOutput: testLogOutput });
      const customCorrelationId = 'health-check-corr-id';

      const response = await request(app)
        .get('/health')
        .set('x-correlation-id', customCorrelationId);

      expect(response.headers['x-correlation-id']).toBe(customCorrelationId);

      const requestLogs = testLogOutput.getRequestLogs();
      const healthLog = requestLogs.find((l) => l.operation === 'GET /health');
      expect(healthLog).toBeDefined();
      expect(healthLog?.correlationId).toBe(customCorrelationId);
      expect(healthLog?.status).toBe('success');
      expect(typeof healthLog?.latencyMs).toBe('number');
    });
  });

  describe('POST /orders', () => {
    it('should create order successfully with valid input', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: 'cust-123',
        items: [
          { productId: 'prod-1', name: 'Widget', quantity: 2, unitPrice: 10.5 },
          { productId: 'prod-2', name: 'Gadget', quantity: 1, unitPrice: 25 },
        ],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(201);

      const order: OrderResponse = response.body;
      expect(order.id).toBeDefined();
      expect(order.customerId).toBe('cust-123');
      expect(order.items).toHaveLength(2);
      expect(order.items[0].subtotal).toBe(21); // 2 * 10.5
      expect(order.items[1].subtotal).toBe(25); // 1 * 25
      expect(order.total).toBe(46);
      expect(order.status).toBe('pending');
      expect(order.createdAt).toBeDefined();
      expect(order.updatedAt).toBeDefined();
    });

    it('should return correlationId in response header', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: 'cust-123',
        items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.headers['x-correlation-id']).toBeDefined();
      expect(typeof response.headers['x-correlation-id']).toBe('string');
    });

    it('should use provided x-correlation-id header', async () => {
      const app = createApp({ logOutput: testLogOutput });
      const providedCorrelationId = 'my-custom-correlation-id-12345';

      const orderRequest: OrderRequest = {
        customerId: 'cust-123',
        items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json')
        .set('x-correlation-id', providedCorrelationId);

      expect(response.headers['x-correlation-id']).toBe(providedCorrelationId);

      // Verify logs contain the same correlationId
      const requestLogs = testLogOutput.getRequestLogs();
      expect(requestLogs.length).toBeGreaterThan(0);
      requestLogs.forEach((log) => {
        expect(log.correlationId).toBe(providedCorrelationId);
      });
    });

    it('should return 400 for invalid input', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: '',
        items: [],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);

      const error: ErrorResponse = response.body;
      expect(error.error).toBe('ValidationError');
      expect(error.message).toContain('customerId is required');
      expect(error.message).toContain('Order must have at least one item');
      expect(error.correlationId).toBeDefined();
    });

    it('should log structured JSON with required fields on success', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: 'cust-123',
        items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
      };

      await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      const requestLogs = testLogOutput.getRequestLogs();
      expect(requestLogs.length).toBeGreaterThan(0);

      const successLog = requestLogs.find((l) => l.status === 'success');
      expect(successLog).toBeDefined();
      expect(successLog?.correlationId).toBeDefined();
      expect(successLog?.operation).toBe('createOrder');
      expect(successLog?.status).toBe('success');
      expect(typeof successLog?.latencyMs).toBe('number');
      expect(successLog?.latencyMs).toBeGreaterThanOrEqual(0);
    });

    it('should log structured JSON with required fields on failure', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: '',
        items: [],
      };

      await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      const requestLogs = testLogOutput.getRequestLogs();
      const failLog = requestLogs.find((l) => l.status === 'fail');

      expect(failLog).toBeDefined();
      expect(failLog?.correlationId).toBeDefined();
      expect(failLog?.operation).toBe('createOrder');
      expect(failLog?.status).toBe('fail');
      expect(typeof failLog?.latencyMs).toBe('number');
    });

    it('should match response shape to OrderResponse contract', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest: OrderRequest = {
        customerId: 'cust-456',
        items: [
          { productId: 'prod-1', name: 'Alpha', quantity: 3, unitPrice: 15.99 },
        ],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(201);

      const order = response.body;

      // Validate all required OrderResponse fields exist and have correct types
      expect(typeof order.id).toBe('string');
      expect(typeof order.customerId).toBe('string');
      expect(Array.isArray(order.items)).toBe(true);
      expect(typeof order.total).toBe('number');
      expect(typeof order.status).toBe('string');
      expect(['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']).toContain(order.status);
      expect(typeof order.createdAt).toBe('string');
      expect(typeof order.updatedAt).toBe('string');

      // Validate item shape
      order.items.forEach((item: Record<string, unknown>) => {
        expect(typeof item.productId).toBe('string');
        expect(typeof item.name).toBe('string');
        expect(typeof item.quantity).toBe('number');
        expect(typeof item.unitPrice).toBe('number');
        expect(typeof item.subtotal).toBe('number');
      });
    });

    it('should return 400 for fractional quantity', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest = {
        customerId: 'cust-123',
        items: [
          { productId: 'prod-1', name: 'Widget', quantity: 1.5, unitPrice: 10 },
        ],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('ValidationError');
      expect(response.body.message).toContain('quantity must be a positive integer');
    });

    it('should return 400 for items with invalid fields', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest = {
        customerId: 'cust-123',
        items: [
          { productId: '', name: 'Widget', quantity: 0, unitPrice: -5 },
        ],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('ValidationError');
    });

    it('should match error response shape to ErrorResponse contract', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const orderRequest = {
        customerId: '',
        items: [],
      };

      const response = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);

      const error = response.body;

      // Validate all required ErrorResponse fields
      expect(typeof error.error).toBe('string');
      expect(typeof error.message).toBe('string');
      expect(typeof error.correlationId).toBe('string');
    });
  });

  describe('GET /orders (list with pagination)', () => {
    it('should return empty list with default pagination', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const response = await request(app).get('/orders');

      expect(response.status).toBe(200);
      expect(response.body.orders).toEqual([]);
      expect(response.body.total).toBe(0);
      expect(response.body.limit).toBe(20);
      expect(response.body.offset).toBe(0);
    });

    it('should return orders with custom pagination', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // Create 3 orders
      for (let i = 0; i < 3; i++) {
        await request(app)
          .post('/orders')
          .send({
            customerId: `cust-${i}`,
            items: [{ productId: `prod-${i}`, name: `Item ${i}`, quantity: 1, unitPrice: 10 }],
          })
          .set('Content-Type', 'application/json');
      }

      // Fetch with limit=2, offset=0
      const response = await request(app).get('/orders?limit=2&offset=0');

      expect(response.status).toBe(200);
      expect(response.body.orders).toHaveLength(2);
      expect(response.body.total).toBe(3);
      expect(response.body.limit).toBe(2);
      expect(response.body.offset).toBe(0);
    });

    it('should return remaining orders with offset', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // Create 3 orders
      for (let i = 0; i < 3; i++) {
        await request(app)
          .post('/orders')
          .send({
            customerId: `cust-${i}`,
            items: [{ productId: `prod-${i}`, name: `Item ${i}`, quantity: 1, unitPrice: 10 }],
          })
          .set('Content-Type', 'application/json');
      }

      // Fetch with limit=2, offset=2
      const response = await request(app).get('/orders?limit=2&offset=2');

      expect(response.status).toBe(200);
      expect(response.body.orders).toHaveLength(1);
      expect(response.body.total).toBe(3);
    });
  });

  describe('PUT /orders/:id', () => {
    it('should update order successfully', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // Create an order first
      const createResponse = await request(app)
        .post('/orders')
        .send({
          customerId: 'cust-123',
          items: [{ productId: 'prod-1', name: 'Widget', quantity: 2, unitPrice: 10 }],
        })
        .set('Content-Type', 'application/json');

      const orderId = createResponse.body.id;

      // Update with new items
      const updateResponse = await request(app)
        .put(`/orders/${orderId}`)
        .send({
          items: [{ productId: 'prod-1', name: 'Widget', quantity: 5, unitPrice: 10 }],
        })
        .set('Content-Type', 'application/json');

      expect(updateResponse.status).toBe(200);
      expect(updateResponse.body.id).toBe(orderId);
      expect(updateResponse.body.items[0].quantity).toBe(5);
      expect(updateResponse.body.total).toBe(50);
      expect(updateResponse.body.updatedAt).toBeDefined();
    });

    it('should return 404 for non-existent order', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const updateResponse = await request(app)
        .put('/orders/nonexistent-id')
        .send({ status: 'confirmed' })
        .set('Content-Type', 'application/json');

      expect(updateResponse.status).toBe(404);
      expect(updateResponse.body.error).toBe('NotFoundError');
    });

    it('should return 400 for invalid input', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // Create an order first
      const createResponse = await request(app)
        .post('/orders')
        .send({
          customerId: 'cust-123',
          items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
        })
        .set('Content-Type', 'application/json');

      const orderId = createResponse.body.id;

      // Update with invalid items
      const updateResponse = await request(app)
        .put(`/orders/${orderId}`)
        .send({
          items: [{ productId: '', name: '', quantity: 0, unitPrice: -1 }],
        })
        .set('Content-Type', 'application/json');

      expect(updateResponse.status).toBe(400);
      expect(updateResponse.body.error).toBe('ValidationError');
    });
  });

  describe('POST /orders/:id/cancel', () => {
    it('should cancel order successfully', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // Create an order
      const createResponse = await request(app)
        .post('/orders')
        .send({
          customerId: 'cust-123',
          items: [{ productId: 'prod-1', name: 'Widget', quantity: 1, unitPrice: 10 }],
        })
        .set('Content-Type', 'application/json');

      const orderId = createResponse.body.id;

      // Cancel it
      const cancelResponse = await request(app)
        .post(`/orders/${orderId}/cancel`);

      expect(cancelResponse.status).toBe(200);
      expect(cancelResponse.body.id).toBe(orderId);
      expect(cancelResponse.body.status).toBe('cancelled');
      expect(cancelResponse.body.updatedAt).toBeDefined();
    });

    it('should return 404 for non-existent order', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const cancelResponse = await request(app)
        .post('/orders/nonexistent-id/cancel');

      expect(cancelResponse.status).toBe(404);
      expect(cancelResponse.body.error).toBe('NotFoundError');
    });
  });

  describe('GET /orders/:id', () => {
    it('should return 200 with order payload for existing order', async () => {
      const app = createApp({ logOutput: testLogOutput });

      // First create an order
      const orderRequest: OrderRequest = {
        customerId: 'cust-123',
        items: [
          { productId: 'prod-1', name: 'Widget', quantity: 2, unitPrice: 10.5 },
        ],
      };

      const createResponse = await request(app)
        .post('/orders')
        .send(orderRequest)
        .set('Content-Type', 'application/json');

      expect(createResponse.status).toBe(201);
      const createdOrder: OrderResponse = createResponse.body;

      // Now fetch it by ID
      const getResponse = await request(app)
        .get(`/orders/${createdOrder.id}`)
        .set('Content-Type', 'application/json');

      expect(getResponse.status).toBe(200);
      expect(getResponse.body.id).toBe(createdOrder.id);
      expect(getResponse.body.customerId).toBe('cust-123');
      expect(getResponse.body.items).toHaveLength(1);
      expect(getResponse.body.total).toBe(21);
      expect(getResponse.body.status).toBe('pending');
      expect(getResponse.body.createdAt).toBeDefined();
      expect(getResponse.body.updatedAt).toBeDefined();
    });

    it('should return 404 for unknown order ID', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const getResponse = await request(app)
        .get('/orders/nonexistent-id-12345')
        .set('Content-Type', 'application/json');

      expect(getResponse.status).toBe(404);
      expect(getResponse.body.error).toBe('NotFoundError');
      expect(getResponse.body.correlationId).toBeDefined();
    });

    it('should return correlationId in response header', async () => {
      const app = createApp({ logOutput: testLogOutput });
      const customCorrelationId = 'get-order-correlation-id';

      const getResponse = await request(app)
        .get('/orders/some-id')
        .set('x-correlation-id', customCorrelationId);

      expect(getResponse.headers['x-correlation-id']).toBe(customCorrelationId);
    });

    it('should return NotFoundError type in error response for missing order', async () => {
      const app = createApp({ logOutput: testLogOutput });

      const response = await request(app)
        .get('/orders/does-not-exist');

      expect(response.status).toBe(404);
      expect(response.body.error).toBe('NotFoundError');
      expect(response.body.message).toContain('Order not found');
      expect(response.body.correlationId).toBeDefined();
    });

    it('should log with required observability fields on not-found', async () => {
      const app = createApp({ logOutput: testLogOutput });
      const correlationId = 'obs-test-correlation';

      await request(app)
        .get('/orders/nonexistent-id')
        .set('x-correlation-id', correlationId);

      const requestLogs = testLogOutput.getRequestLogs();
      const failLog = requestLogs.find((l) => l.operation === 'getOrderById' && l.status === 'fail');
      expect(failLog).toBeDefined();
      expect(failLog?.correlationId).toBe(correlationId);
      expect(typeof failLog?.latencyMs).toBe('number');
    });
  });
});
