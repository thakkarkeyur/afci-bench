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

// Pagination DTOs
export interface ListOrdersRequest {
  limit?: number;
  offset?: number;
}

export interface ListOrdersResponse {
  orders: OrderResponse[];
  total: number;
  limit: number;
  offset: number;
}

// Repository port interface (shared across layers)
export interface OrderData {
  id: string;
  customerId: string;
  items: OrderItemData[];
  total: number;
  status: OrderStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface OrderItemData {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface OrderRepositoryPort {
  save(order: OrderData): Promise<OrderData>;
  findById(id: string): Promise<OrderData | null>;
  findByCustomerId(customerId: string): Promise<OrderData[]>;
  findAll(limit: number, offset: number): Promise<{ orders: OrderData[]; total: number }>;
}

// Error response contract
export interface ErrorResponse {
  error: string;
  message: string;
  correlationId: string;
}

// Health check response
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'unhealthy';
  timestamp: string;
}
