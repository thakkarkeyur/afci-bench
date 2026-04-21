import { v4 as uuidv4 } from 'uuid';
import { OrderRequest, OrderResponse, ListOrdersResponse } from '@afci-bench/contracts';
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
