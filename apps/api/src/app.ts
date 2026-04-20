import express, { Express, Request, Response, NextFunction } from 'express';
import { OrderRequest, OrderResponse, ErrorResponse, HealthResponse } from '@afci-bench/contracts';
import { createOrderUseCase, CreateOrderPorts, getOrderByIdUseCase, GetOrderByIdPorts, listOrdersUseCase, ListOrdersPorts, Order, OrderRepository } from '@afci-bench/features';
import { getOrderRepository, OrderEntity } from '@afci-bench/infra';
import {
  Logger,
  LogOutput,
  extractCorrelationId,
  ConsoleLogOutput,
} from '@afci-bench/observability';

// NOTE: This file imports Order/OrderRepository from @afci-bench/features (which re-exports from core)
// instead of importing directly from @afci-bench/core. This respects the module boundary rules:
// apps/api can depend on features, but should not depend on core directly.
//
// BOUNDARY VIOLATION EXAMPLE (commented out - would fail CI if uncommented):
// import { Order } from '@afci-bench/core'; // ERROR: api cannot import core directly

// Adapter to convert infra's OrderEntity to core's Order
function adaptRepository(infraRepo: ReturnType<typeof getOrderRepository>): OrderRepository {
  return {
    async save(order: Order): Promise<Order> {
      const entity: OrderEntity = {
        id: order.id,
        customerId: order.customerId,
        items: order.items,
        total: order.total,
        status: order.status,
        createdAt: order.createdAt,
      };
      const saved = await infraRepo.save(entity);
      return {
        id: saved.id,
        customerId: saved.customerId,
        items: saved.items,
        total: saved.total,
        status: saved.status,
        createdAt: saved.createdAt,
      };
    },
    async findById(id: string): Promise<Order | null> {
      const entity = await infraRepo.findById(id);
      if (!entity) return null;
      return {
        id: entity.id,
        customerId: entity.customerId,
        items: entity.items,
        total: entity.total,
        status: entity.status,
        createdAt: entity.createdAt,
      };
    },
    async findByCustomerId(customerId: string): Promise<Order[]> {
      const entities = await infraRepo.findByCustomerId(customerId);
      return entities.map((entity) => ({
        id: entity.id,
        customerId: entity.customerId,
        items: entity.items,
        total: entity.total,
        status: entity.status,
        createdAt: entity.createdAt,
      }));
    },
    async findAll(limit: number, offset: number): Promise<{ data: Order[]; total: number }> {
      const result = await infraRepo.findAll(limit, offset);
      return {
        data: result.data.map((entity) => ({
          id: entity.id,
          customerId: entity.customerId,
          items: entity.items,
          total: entity.total,
          status: entity.status,
          createdAt: entity.createdAt,
        })),
        total: result.total,
      };
    },
  };
}

export interface AppDependencies {
  logOutput?: LogOutput;
}

export function createApp(deps: AppDependencies = {}): Express {
  const app = express();
  const logOutput = deps.logOutput ?? new ConsoleLogOutput();
  const logger = new Logger(logOutput);
  const orderRepository = adaptRepository(getOrderRepository());

  app.use(express.json());

  // Health endpoint
  app.get('/health', (_req: Request, res: Response) => {
    const response: HealthResponse = {
      status: 'ok',
      timestamp: new Date().toISOString(),
    };
    res.json(response);
  });

  // Create order endpoint
  app.post('/orders', async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const correlationId = extractCorrelationId(req.headers['x-correlation-id'] as string | undefined);

    try {
      const input: OrderRequest = req.body;

      const ports: CreateOrderPorts = {
        orderRepository,
        logger,
        correlationId,
      };

      const result = await createOrderUseCase(input, ports);

      if (result.success && result.data) {
        const response: OrderResponse = result.data;
        res.setHeader('x-correlation-id', correlationId);
        res.status(201).json(response);
      } else {
        const errorResponse: ErrorResponse = {
          error: 'ValidationError',
          message: result.errors?.join('; ') ?? 'Unknown validation error',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(400).json(errorResponse);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Internal server error';

      logger.logError({
        correlationId,
        errorType: 'UnhandledError',
        message: errorMessage,
        stack: error instanceof Error ? error.stack : undefined,
      });

      logger.logRequest({
        correlationId,
        operation: 'POST /orders',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      const errorResponse: ErrorResponse = {
        error: 'InternalServerError',
        message: errorMessage,
        correlationId,
      };
      res.setHeader('x-correlation-id', correlationId);
      res.status(500).json(errorResponse);
      next(error);
    }
  });

  // List orders with pagination
  app.get('/orders', async (req: Request, res: Response, next: NextFunction) => {
    const correlationId = extractCorrelationId(req.headers['x-correlation-id'] as string | undefined);

    try {
      const limit = parseInt(req.query.limit as string, 10) || 20;
      const offset = parseInt(req.query.offset as string, 10) || 0;

      const ports: ListOrdersPorts = {
        orderRepository,
        logger,
        correlationId,
      };

      const result = await listOrdersUseCase(limit, offset, ports);
      res.setHeader('x-correlation-id', correlationId);
      res.status(200).json(result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Internal server error';
      const errorResponse: ErrorResponse = {
        error: 'InternalServerError',
        message: errorMessage,
        correlationId,
      };
      res.setHeader('x-correlation-id', correlationId);
      res.status(500).json(errorResponse);
      next(error);
    }
  });

  // Get order by ID endpoint
  app.get('/orders/:id', async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const correlationId = extractCorrelationId(req.headers['x-correlation-id'] as string | undefined);

    try {
      const ports: GetOrderByIdPorts = {
        orderRepository,
        logger,
        correlationId,
      };

      const result = await getOrderByIdUseCase(req.params.id, ports);

      if (result.success && result.data) {
        const response: OrderResponse = result.data;
        res.setHeader('x-correlation-id', correlationId);
        res.status(200).json(response);
      } else if (result.notFound) {
        const errorResponse: ErrorResponse = {
          error: 'NotFound',
          message: result.errors?.join('; ') ?? 'Order not found',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(404).json(errorResponse);
      } else {
        const errorResponse: ErrorResponse = {
          error: 'ValidationError',
          message: result.errors?.join('; ') ?? 'Unknown error',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(400).json(errorResponse);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Internal server error';

      logger.logError({
        correlationId,
        errorType: 'UnhandledError',
        message: errorMessage,
        stack: error instanceof Error ? error.stack : undefined,
      });

      logger.logRequest({
        correlationId,
        operation: 'GET /orders/:id',
        status: 'fail',
        latencyMs: Date.now() - startTime,
      });

      const errorResponse: ErrorResponse = {
        error: 'InternalServerError',
        message: errorMessage,
        correlationId,
      };
      res.setHeader('x-correlation-id', correlationId);
      res.status(500).json(errorResponse);
      next(error);
    }
  });

  return app;
}
