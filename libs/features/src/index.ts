import { v4 as uuidv4 } from 'uuid';
import { OrderRequest, OrderResponse, ListOrdersResponse, UpdateOrderRequest } from '@afci-bench/contracts';
import {
  Order,
  OrderItem,
  OrderRepository,
  createOrderItem,
  calculateOrderTotal,
  validateOrderItems,
  validateCustomerId,
  mapOrderToResponse,
} from '@afci-bench/core';
import { Logger } from '@afci-bench/observability';

// Re-export types from core that the API layer needs
// This allows API to depend on features without directly importing core
export type { Order, OrderItem, OrderRepository };
export { mapOrderToResponse };

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
    const order = await orderRepository.findById(orderId);

    if (!order) {
      logger.logRequest({
        correlationId,
        operation: 'getOrderById',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      return {
        success: false,
        notFound: true,
        errors: [`Order not found: ${orderId}`],
      };
    }

    const response: OrderResponse = mapOrderToResponse(order);

    logger.logRequest({
      correlationId,
      operation: 'getOrderById',
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

    return {
      success: false,
      errors: [errorMessage],
    };
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

    const now = new Date();
    const order: Order = {
      id: uuidv4(),
      customerId: input.customerId,
      items: orderItems,
      total,
      status: 'pending',
      createdAt: now,
      updatedAt: now,
    };

    // Persist via repository
    const savedOrder = await orderRepository.save(order);

    // Map to response DTO
    const response: OrderResponse = mapOrderToResponse(savedOrder);

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

export interface ListOrdersPorts {
  orderRepository: OrderRepository;
  logger: Logger;
  correlationId: string;
}

export interface ListOrdersResult {
  success: boolean;
  data?: ListOrdersResponse;
  errors?: string[];
}

const DEFAULT_LIMIT = 20;
const DEFAULT_OFFSET = 0;

export async function listOrdersUseCase(
  limit: number | undefined,
  offset: number | undefined,
  ports: ListOrdersPorts
): Promise<ListOrdersResult> {
  const startTime = Date.now();
  const { orderRepository, logger, correlationId } = ports;
  const effectiveLimit = limit ?? DEFAULT_LIMIT;
  const effectiveOffset = offset ?? DEFAULT_OFFSET;

  try {
    const { orders, total } = await orderRepository.findAll(effectiveLimit, effectiveOffset);

    const response: ListOrdersResponse = {
      orders: orders.map(mapOrderToResponse),
      total,
      limit: effectiveLimit,
      offset: effectiveOffset,
    };

    logger.logRequest({
      correlationId,
      operation: 'listOrders',
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
      errorType: 'ListOrdersError',
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
    });

    logger.logRequest({
      correlationId,
      operation: 'listOrders',
      status: 'fail',
      latencyMs: Date.now() - startTime,
    });

    return {
      success: false,
      errors: [errorMessage],
    };
  }
}

export interface UpdateOrderPorts {
  orderRepository: OrderRepository;
  logger: Logger;
  correlationId: string;
}

export interface UpdateOrderResult {
  success: boolean;
  data?: OrderResponse;
  notFound?: boolean;
  errors?: string[];
}

export async function updateOrderUseCase(
  orderId: string,
  input: UpdateOrderRequest,
  ports: UpdateOrderPorts
): Promise<UpdateOrderResult> {
  const startTime = Date.now();
  const { orderRepository, logger, correlationId } = ports;

  try {
    const existing = await orderRepository.findById(orderId);

    if (!existing) {
      logger.logRequest({
        correlationId,
        operation: 'updateOrder',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      return {
        success: false,
        notFound: true,
        errors: [`Order not found: ${orderId}`],
      };
    }

    // Validate updated items if provided
    if (input.items !== undefined) {
      const itemsValidation = validateOrderItems(input.items);
      if (!itemsValidation.valid) {
        logger.logRequest({
          correlationId,
          operation: 'updateOrder',
          status: 'fail',
          latencyMs: Date.now() - startTime,
        });

        return {
          success: false,
          errors: itemsValidation.errors,
        };
      }
    }

    // Apply updates
    const updatedItems = input.items
      ? input.items.map(createOrderItem)
      : existing.items;
    const updatedTotal = input.items
      ? calculateOrderTotal(updatedItems)
      : existing.total;
    const updatedStatus = input.status ?? existing.status;

    const updatedOrder: Order = {
      ...existing,
      items: updatedItems,
      total: updatedTotal,
      status: updatedStatus,
      updatedAt: new Date(),
    };

    const saved = await orderRepository.update(updatedOrder);
    const response: OrderResponse = mapOrderToResponse(saved);

    logger.logRequest({
      correlationId,
      operation: 'updateOrder',
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
      errorType: 'UpdateOrderError',
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
    });

    logger.logRequest({
      correlationId,
      operation: 'updateOrder',
      status: 'fail',
      latencyMs: Date.now() - startTime,
    });

    return {
      success: false,
      errors: [errorMessage],
    };
  }
}

export interface CancelOrderPorts {
  orderRepository: OrderRepository;
  logger: Logger;
  correlationId: string;
}

export interface CancelOrderResult {
  success: boolean;
  data?: OrderResponse;
  notFound?: boolean;
  errors?: string[];
}

export async function cancelOrderUseCase(
  orderId: string,
  ports: CancelOrderPorts
): Promise<CancelOrderResult> {
  const startTime = Date.now();
  const { orderRepository, logger, correlationId } = ports;

  try {
    const existing = await orderRepository.findById(orderId);

    if (!existing) {
      logger.logRequest({
        correlationId,
        operation: 'cancelOrder',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      return {
        success: false,
        notFound: true,
        errors: [`Order not found: ${orderId}`],
      };
    }

    const cancelledOrder: Order = {
      ...existing,
      status: 'cancelled',
      updatedAt: new Date(),
    };

    const saved = await orderRepository.update(cancelledOrder);
    const response: OrderResponse = mapOrderToResponse(saved);

    logger.logRequest({
      correlationId,
      operation: 'cancelOrder',
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
      errorType: 'CancelOrderError',
      message: errorMessage,
      stack: error instanceof Error ? error.stack : undefined,
    });

    logger.logRequest({
      correlationId,
      operation: 'cancelOrder',
      status: 'fail',
      latencyMs: Date.now() - startTime,
    });

    return {
      success: false,
      errors: [errorMessage],
    };
  }
}
