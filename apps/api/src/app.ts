import express, { Express, Request, Response, NextFunction } from 'express';
import { OrderRequest, OrderResponse, ErrorResponse, HealthResponse } from '@afci-bench/contracts';
import { createOrderUseCase, CreateOrderPorts, getOrderByIdUseCase, GetOrderByIdPorts, listOrdersUseCase, ListOrdersPorts } from '@afci-bench/features';
import { getOrderRepository } from '@afci-bench/infra';
import {
  Logger,
  LogOutput,
  extractCorrelationId,
  ConsoleLogOutput,
} from '@afci-bench/observability';

// NOTE: This file imports OrderRepository from @afci-bench/features (which re-exports from core)
// instead of importing directly from @afci-bench/core. This respects the module boundary rules:
// apps/api can depend on features, but should not depend on core directly.
//
// Since T03, the OrderRepositoryPort lives in @afci-bench/contracts. Both infra's
// InMemoryOrderRepository and core's OrderRepository type alias point to the same
// contracts port, so the infra repo can be used directly — no adapter needed.

export interface AppDependencies {
  logOutput?: LogOutput;
}

export function createApp(deps: AppDependencies = {}): Express {
  const app = express();
  const logOutput = deps.logOutput ?? new ConsoleLogOutput();
  const logger = new Logger(logOutput);
  const orderRepository = getOrderRepository();

  app.use(express.json());

  // Health endpoint
  app.get('/health', (req: Request, res: Response) => {
    const startTime = Date.now();
    const correlationId = extractCorrelationId(req.headers['x-correlation-id'] as string | undefined);

    const response: HealthResponse = {
      status: 'ok',
      timestamp: new Date().toISOString(),
    };

    logger.logRequest({
      correlationId,
      operation: 'GET /health',
      status: 'success',
      latencyMs: Date.now() - startTime,
    });

    res.setHeader('x-correlation-id', correlationId);
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

  // List orders endpoint
  app.get('/orders', async (req: Request, res: Response) => {
    const startTime = Date.now();
    const correlationId = extractCorrelationId(req.headers['x-correlation-id'] as string | undefined);

    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
      const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;

      const ports: ListOrdersPorts = {
        orderRepository,
        logger,
        correlationId,
      };

      const result = await listOrdersUseCase(limit, offset, ports);

      if (result.success && result.data) {
        res.setHeader('x-correlation-id', correlationId);
        res.status(200).json(result.data);
      } else {
        const errorResponse: ErrorResponse = {
          error: 'InternalServerError',
          message: result.errors?.join('; ') ?? 'Unknown error',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(500).json(errorResponse);
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
        operation: 'GET /orders',
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
    }
  });

  // Get order by ID endpoint
  app.get('/orders/:id', async (req: Request, res: Response) => {
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
        res.setHeader('x-correlation-id', correlationId);
        res.status(200).json(result.data);
      } else if (result.notFound) {
        const errorResponse: ErrorResponse = {
          error: 'NotFoundError',
          message: result.errors?.join('; ') ?? 'Order not found',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(404).json(errorResponse);
      } else {
        const errorResponse: ErrorResponse = {
          error: 'InternalServerError',
          message: result.errors?.join('; ') ?? 'Unknown error',
          correlationId,
        };
        res.setHeader('x-correlation-id', correlationId);
        res.status(500).json(errorResponse);
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
    }
  });

  return app;
}
