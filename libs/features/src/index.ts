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

// Re-export types from core that the API layer needs
// This allows API to depend on features without directly importing core
export type { Order, OrderItem, OrderRepository };

export interface GetOrderByIdPorts {
  orderRepository: OrderRepository;
  logger: Logger;
  correlationId: string;
}

export interface GetOrderByIdResult {
  success: boolean;
  data?: OrderResponse;
  notFound?: boolean;
  errors?: string[];
}

export async function getOrderByIdUseCase(
  orderId: string,
  ports: GetOrderByIdPorts
): Promise<GetOrderByIdResult> {
  const startTime = Date.now();
  const { orderRepository, logger, correlationId } = ports;

  try {
    if (!orderId || orderId.trim() === '') {
      logger.logRequest({
        correlationId,
        operation: 'getOrderById',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });
      return { success: false, errors: ['orderId is required'] };
    }

    const order = await orderRepository.findById(orderId);

    if (!order) {
      logger.logRequest({
        correlationId,
        operation: 'getOrderById',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });
      return { success: false, notFound: true, errors: ['Order not found'] };
    }

    const responseItems: OrderItemResponse[] = order.items.map((item) => ({
      productId: item.productId,
      name: item.name,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      subtotal: item.subtotal,
    }));

    const response: OrderResponse = {
      id: order.id,
      customerId: order.customerId,
      items: responseItems,
      total: order.total,
      status: order.status,
      createdAt: order.createdAt.toISOString(),
    };

    logger.logRequest({
      correlationId,
      operation: 'getOrderById',
      status: 'success',
      latencyMs: Date.now() - startTime,
    });

    return { success: true, data: response };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    logger.logError({
      correlationId,
      errorType: 'GetOrderByIdError',
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
    });

    logger.logRequest({
      correlationId,
      operation: 'getOrderById',
      status: 'fail',
      latencyMs: Date.now() - startTime,
    });

    return { success: false, errors: [errorMessage] };
  }
}

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
