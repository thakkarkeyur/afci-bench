import { v4 as uuidv4 } from 'uuid';

export interface RequestLogEntry {
  correlationId: string;
  operation: string;
  status: 'success' | 'fail';
  latencyMs: number;
  timestamp: string;
}

export interface ErrorLogEntry {
  correlationId: string;
  errorType: string;
  message: string;
  timestamp: string;
  stack?: string;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogOutput {
  write(level: LogLevel, entry: RequestLogEntry | ErrorLogEntry): void;
}

export class ConsoleLogOutput implements LogOutput {
  write(level: LogLevel, entry: RequestLogEntry | ErrorLogEntry): void {
    const logFn = level === 'error' ? console.error : console.log;
    logFn(JSON.stringify(entry));
  }
}

export class Logger {
  private output: LogOutput;

  constructor(output?: LogOutput) {
    this.output = output ?? new ConsoleLogOutput();
  }

  logRequest(entry: Omit<RequestLogEntry, 'timestamp'>): void {
    const fullEntry: RequestLogEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
    };
    this.output.write(entry.status === 'fail' ? 'error' : 'info', fullEntry);
  }

  logError(entry: Omit<ErrorLogEntry, 'timestamp'>): void {
    const fullEntry: ErrorLogEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
    };
    this.output.write('error', fullEntry);
  }
}

export function extractCorrelationId(headerValue: string | undefined): string {
  if (headerValue && typeof headerValue === 'string' && headerValue.trim().length > 0) {
    return headerValue.trim();
  }
  return uuidv4();
}

export function createLogger(output?: LogOutput): Logger {
  return new Logger(output);
}
