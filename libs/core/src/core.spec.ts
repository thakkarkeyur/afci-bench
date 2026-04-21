import {
  calculateItemSubtotal,
  calculateOrderTotal,
  createOrderItem,
  validateOrderItems,
  validateCustomerId,
  mapOrderToResponse,
  mapOrderItemToResponse,
  OrderItem,
  Order,
} from './index';
import { OrderItemRequest } from '@afci-bench/contracts';

describe('calculateItemSubtotal', () => {
  it('should calculate subtotal correctly', () => {
    expect(calculateItemSubtotal(2, 10.5)).toBe(21);
  });

  it('should handle zero quantity', () => {
    expect(calculateItemSubtotal(0, 10)).toBe(0);
  });

  it('should handle zero price', () => {
    expect(calculateItemSubtotal(5, 0)).toBe(0);
  });

  it('should round to 2 decimal places', () => {
    expect(calculateItemSubtotal(3, 10.333)).toBe(31);
  });

  it('should throw error for negative quantity', () => {
    expect(() => calculateItemSubtotal(-1, 10)).toThrow(
      'Quantity and unit price must be non-negative'
    );
  });

  it('should throw error for negative price', () => {
    expect(() => calculateItemSubtotal(1, -10)).toThrow(
      'Quantity and unit price must be non-negative'
    );
  });
});

describe('calculateOrderTotal', () => {
  it('should sum all item subtotals', () => {
    const items: OrderItem[] = [
      { productId: '1', name: 'A', quantity: 1, unitPrice: 10, subtotal: 10 },
      { productId: '2', name: 'B', quantity: 2, unitPrice: 5, subtotal: 10 },
      { productId: '3', name: 'C', quantity: 1, unitPrice: 15, subtotal: 15 },
    ];
    expect(calculateOrderTotal(items)).toBe(35);
  });

  it('should return 0 for empty items', () => {
    expect(calculateOrderTotal([])).toBe(0);
  });

  it('should handle single item', () => {
    const items: OrderItem[] = [
      { productId: '1', name: 'A', quantity: 1, unitPrice: 25.5, subtotal: 25.5 },
    ];
    expect(calculateOrderTotal(items)).toBe(25.5);
  });
});

describe('createOrderItem', () => {
  it('should create order item with calculated subtotal', () => {
    const input = {
      productId: 'prod-123',
      name: 'Test Product',
      quantity: 3,
      unitPrice: 15.5,
    };

    const result = createOrderItem(input);

    expect(result).toEqual({
      productId: 'prod-123',
      name: 'Test Product',
      quantity: 3,
      unitPrice: 15.5,
      subtotal: 46.5,
    });
  });
});

describe('validateOrderItems', () => {
  it('should return valid for correct items', () => {
    const items = [
      { productId: 'p1', name: 'Item 1', quantity: 1, unitPrice: 10 },
    ];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should reject empty items array', () => {
    const result = validateOrderItems([]);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Order must have at least one item');
  });

  it('should reject missing productId', () => {
    const items = [{ productId: '', name: 'Item', quantity: 1, unitPrice: 10 }];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Item 1: productId is required');
  });

  it('should reject missing name', () => {
    const items = [{ productId: 'p1', name: '', quantity: 1, unitPrice: 10 }];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Item 1: name is required');
  });

  it('should reject zero or negative quantity', () => {
    const items = [{ productId: 'p1', name: 'Item', quantity: 0, unitPrice: 10 }];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Item 1: quantity must be a positive integer');
  });

  it('should reject negative unitPrice', () => {
    const items = [{ productId: 'p1', name: 'Item', quantity: 1, unitPrice: -5 }];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Item 1: unitPrice must be a non-negative number');
  });

  it('should reject fractional quantity', () => {
    const items = [{ productId: 'p1', name: 'Item', quantity: 1.5, unitPrice: 10 }];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Item 1: quantity must be a positive integer');
  });

  it('should handle null items gracefully', () => {
    const result = validateOrderItems(null as unknown as OrderItemRequest[]);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Order must have at least one item');
  });

  it('should handle undefined items gracefully', () => {
    const result = validateOrderItems(undefined as unknown as OrderItemRequest[]);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Order must have at least one item');
  });

  it('should collect multiple errors', () => {
    const items = [
      { productId: '', name: '', quantity: 0, unitPrice: -1 },
    ];
    const result = validateOrderItems(items);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThanOrEqual(4);
  });
});

describe('validateCustomerId', () => {
  it('should return valid for non-empty customerId', () => {
    const result = validateCustomerId('cust-123');
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should reject empty customerId', () => {
    const result = validateCustomerId('');
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('customerId is required');
  });

  it('should reject whitespace-only customerId', () => {
    const result = validateCustomerId('   ');
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('customerId is required');
  });
});

describe('mapOrderToResponse', () => {
  it('should map Order to OrderResponse correctly', () => {
    const now = new Date('2024-01-15T10:30:00.000Z');
    const order: Order = {
      id: 'order-1',
      customerId: 'cust-1',
      items: [
        { productId: 'p1', name: 'Widget', quantity: 2, unitPrice: 10, subtotal: 20 },
      ],
      total: 20,
      status: 'created',
      createdAt: now,
      updatedAt: now,
    };

    const response = mapOrderToResponse(order);

    expect(response.id).toBe('order-1');
    expect(response.customerId).toBe('cust-1');
    expect(response.items).toHaveLength(1);
    expect(response.items[0].subtotal).toBe(20);
    expect(response.total).toBe(20);
    expect(response.status).toBe('created');
    expect(response.createdAt).toBe('2024-01-15T10:30:00.000Z');
    expect(response.updatedAt).toBe('2024-01-15T10:30:00.000Z');
  });
});

describe('mapOrderItemToResponse', () => {
  it('should map OrderItem to OrderItemResponse correctly', () => {
    const item: OrderItem = {
      productId: 'p1',
      name: 'Widget',
      quantity: 3,
      unitPrice: 15,
      subtotal: 45,
    };

    const response = mapOrderItemToResponse(item);

    expect(response.productId).toBe('p1');
    expect(response.name).toBe('Widget');
    expect(response.quantity).toBe(3);
    expect(response.unitPrice).toBe(15);
    expect(response.subtotal).toBe(45);
  });
});
