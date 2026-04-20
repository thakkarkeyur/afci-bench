// Order DTOs - Public API contracts
export interface OrderItemRequest {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
}

export interface OrderRequest {
  customerId: string;
  items: OrderItemRequest[];
}

export interface OrderItemResponse {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface OrderResponse {
  id: string;
  customerId: string;
  items: OrderItemResponse[];
  total: number;
  status: OrderStatus;
  createdAt: string;
  updatedAt: string;
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';

export interface UpdateOrderRequest {
  status?: OrderStatus;
}

// Error response contract
export interface ErrorResponse {
  error: string;
  message: string;
  correlationId: string;
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

// Order entity shape (shared port type)
export interface OrderEntity {
  id: string;
  customerId: string;
  items: OrderItemResponse[];
  total: number;
  status: OrderStatus;
  createdAt: Date;
  updatedAt: Date;
}

// Repository port interface - lives in contracts per MAD
export interface OrderRepositoryPort {
  save(order: OrderEntity): Promise<OrderEntity>;
  findById(id: string): Promise<OrderEntity | null>;
  findByCustomerId(customerId: string): Promise<OrderEntity[]>;
  findAll(limit: number, offset: number): Promise<{ data: OrderEntity[]; total: number }>;
  update(id: string, fields: Partial<Pick<OrderEntity, 'status' | 'updatedAt'>>): Promise<OrderEntity | null>;
}

// Health check response
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'unhealthy';
  timestamp: string;
}
