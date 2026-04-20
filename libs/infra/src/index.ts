import { OrderStatus } from '@afci-bench/contracts';

// Infra layer implements repository interfaces
// Note: We define our own Order type here based on contracts to avoid importing from core
// This is a deliberate architectural choice - infra depends on contracts, not core

export interface OrderEntity {
  id: string;
  customerId: string;
  items: OrderItemEntity[];
  total: number;
  status: OrderStatus;
  createdAt: Date;
}

export interface OrderItemEntity {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

// Port interface (matching core's OrderRepository)
export interface OrderRepositoryPort {
  save(order: OrderEntity): Promise<OrderEntity>;
  findById(id: string): Promise<OrderEntity | null>;
  findByCustomerId(customerId: string): Promise<OrderEntity[]>;
  findAll(limit: number, offset: number): Promise<{ data: OrderEntity[]; total: number }>;
}

export class InMemoryOrderRepository implements OrderRepositoryPort {
  private orders: Map<string, OrderEntity> = new Map();

  async save(order: OrderEntity): Promise<OrderEntity> {
    const savedOrder = { ...order };
    this.orders.set(order.id, savedOrder);
    return savedOrder;
  }

  async findById(id: string): Promise<OrderEntity | null> {
    return this.orders.get(id) ?? null;
  }

  async findByCustomerId(customerId: string): Promise<OrderEntity[]> {
    const results: OrderEntity[] = [];
    this.orders.forEach((order) => {
      if (order.customerId === customerId) {
        results.push(order);
      }
    });
    return results;
  }

  async findAll(limit: number, offset: number): Promise<{ data: OrderEntity[]; total: number }> {
    const all = Array.from(this.orders.values());
    all.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
    const total = all.length;
    const data = all.slice(offset, offset + limit);
    return { data, total };
  }

  // Test helper - not part of interface
  clear(): void {
    this.orders.clear();
  }

  // Test helper - get count
  count(): number {
    return this.orders.size;
  }
}

// Singleton instance for simple use cases
let defaultRepository: InMemoryOrderRepository | null = null;

export function getOrderRepository(): InMemoryOrderRepository {
  if (!defaultRepository) {
    defaultRepository = new InMemoryOrderRepository();
  }
  return defaultRepository;
}

export function resetOrderRepository(): void {
  if (defaultRepository) {
    defaultRepository.clear();
  }
  defaultRepository = null;
}
