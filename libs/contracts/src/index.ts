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
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';

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

// Health check response
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'unhealthy';
  timestamp: string;
}
