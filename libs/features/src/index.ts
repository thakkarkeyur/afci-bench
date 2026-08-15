import { v4 as uuidv4 } from 'uuid';
import { OrderRequest, OrderResponse, OrderItemResponse } from '@afci-bench/contracts';
import {
  Order,
  OrderItem,
  OrderRepository,
  createOrderItem,
  calculateOrderTotal,
  validateOrderItems,
  validateCustomerId,
} from '@afci-bench/core';
import { Logger } from '@afci-bench/observability';

// Re-export the domain types that callers of this use case work with
export type { Order, OrderItem, OrderRepository };

export interface CreateOrderPorts {
  orderRepository: OrderRepository;
  logger: Logger;
  correlationId: string;
}

export interface CreateOrderResult {
  success: boolean;
  data?: OrderResponse;
  errors?: string[];
}

export async function createOrderUseCase(
  input: OrderRequest,
  ports: CreateOrderPorts
): Promise<CreateOrderResult> {
  const startTime = Date.now();
  const { orderRepository, logger, correlationId } = ports;

  try {
    // Validate input
    const customerValidation = validateCustomerId(input.customerId);
    const itemsValidation = validateOrderItems(input.items);

    if (!customerValidation.valid || !itemsValidation.valid) {
      const allErrors = [...customerValidation.errors, ...itemsValidation.errors];

      logger.logRequest({
        correlationId,
        operation: 'createOrder',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      return {
        success: false,
        errors: allErrors,
      };
    }

    // Create domain entities
    const orderItems = input.items.map(createOrderItem);
    const total = calculateOrderTotal(orderItems);

    const order: Order = {
      id: uuidv4(),
      customerId: input.customerId,
      items: orderItems,
      total,
      status: 'pending',
      createdAt: new Date(),
    };

    // Persist via repository
    const savedOrder = await orderRepository.save(order);

    // Map to response DTO
    const responseItems: OrderItemResponse[] = savedOrder.items.map((item) => ({
      productId: item.productId,
      name: item.name,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      subtotal: item.subtotal,
    }));

    const response: OrderResponse = {
      id: savedOrder.id,
      customerId: savedOrder.customerId,
      items: responseItems,
      total: savedOrder.total,
      status: savedOrder.status,
      createdAt: savedOrder.createdAt.toISOString(),
    };

    logger.logRequest({
      correlationId,
      operation: 'createOrder',
      status: 'success',
      latencyMs: Date.now() - startTime,
    });

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    logger.logError({
      correlationId,
      errorType: 'CreateOrderError',
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
    });

    logger.logRequest({
      correlationId,
      operation: 'createOrder',
      status: 'fail',
      latencyMs: Date.now() - startTime,
    });

    return {
      success: false,
      errors: [errorMessage],
    };
  }
}
