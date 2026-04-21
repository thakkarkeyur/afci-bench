import { OrderItemRequest, OrderStatus, OrderRepositoryPort } from '@afci-bench/contracts';

// Domain entity (internal representation)
export interface OrderItem {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface Order {
  id: string;
  customerId: string;
  items: OrderItem[];
  total: number;
  status: OrderStatus;
  createdAt: Date;
  updatedAt: Date;
}

// OrderRepository is the domain's view of the port defined in contracts.
// Order is structurally compatible with OrderData, so this alias works.
export type OrderRepository = OrderRepositoryPort;

// Validation result
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

// Pure domain functions
export function calculateItemSubtotal(quantity: number, unitPrice: number): number {
  if (quantity < 0 || unitPrice < 0) {
    throw new Error('Quantity and unit price must be non-negative');
  }
  return Math.round(quantity * unitPrice * 100) / 100;
}

export function calculateOrderTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.subtotal, 0);
}

export function createOrderItem(input: OrderItemRequest): OrderItem {
  const subtotal = calculateItemSubtotal(input.quantity, input.unitPrice);
  return {
    productId: input.productId,
    name: input.name,
    quantity: input.quantity,
    unitPrice: input.unitPrice,
    subtotal,
  };
}

export function validateOrderItems(items: OrderItemRequest[]): ValidationResult {
  const errors: string[] = [];

  if (!items || !Array.isArray(items) || items.length === 0) {
    errors.push('Order must have at least one item');
    return { valid: false, errors };
  }

  items.forEach((item, index) => {
    if (!item.productId || item.productId.trim() === '') {
      errors.push(`Item ${index + 1}: productId is required`);
    }
    if (!item.name || item.name.trim() === '') {
      errors.push(`Item ${index + 1}: name is required`);
    }
    if (typeof item.quantity !== 'number' || item.quantity <= 0 || !Number.isInteger(item.quantity)) {
      errors.push(`Item ${index + 1}: quantity must be a positive integer`);
    }
    if (typeof item.unitPrice !== 'number' || item.unitPrice < 0) {
      errors.push(`Item ${index + 1}: unitPrice must be a non-negative number`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function validateCustomerId(customerId: string): ValidationResult {
  const errors: string[] = [];

  if (!customerId || customerId.trim() === '') {
    errors.push('customerId is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
