import { OrderEntity, OrderRepositoryPort } from '@afci-bench/contracts';

// Re-export for backwards compatibility
export type { OrderEntity };
export type { OrderRepositoryPort };

// Also export the old OrderItemEntity name for any consumers
export type OrderItemEntity = OrderEntity['items'][number];

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

  async update(id: string, fields: Partial<Pick<OrderEntity, 'status' | 'updatedAt'>>): Promise<OrderEntity | null> {
    const existing = this.orders.get(id);
    if (!existing) return null;
    const updated = { ...existing, ...fields };
    this.orders.set(id, updated);
    return updated;
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
