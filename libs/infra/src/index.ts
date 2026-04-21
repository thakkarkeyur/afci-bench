import { OrderData, OrderItemData, OrderRepositoryPort } from '@afci-bench/contracts';

// Infra layer implements the shared OrderRepositoryPort from contracts.
// OrderEntity/OrderItemEntity are kept as aliases for backwards compatibility.
export type OrderEntity = OrderData;
export type OrderItemEntity = OrderItemData;

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

  async update(order: OrderEntity): Promise<OrderEntity> {
    const updatedOrder = { ...order };
    this.orders.set(order.id, updatedOrder);
    return updatedOrder;
  }

  async findAll(limit: number, offset: number): Promise<{ orders: OrderEntity[]; total: number }> {
    const all = Array.from(this.orders.values());
    const total = all.length;
    const orders = all.slice(offset, offset + limit);
    return { orders, total };
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
