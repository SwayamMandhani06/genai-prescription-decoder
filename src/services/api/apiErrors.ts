import { FastApiHttpErrorDto, FastApiValidationErrorDetail } from '../../types/api.types';

/**
 * Base Application API Error
 */
export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly errorResponse?: FastApiHttpErrorDto;
  public readonly requestId?: string;

  constructor(
    message: string,
    statusCode: number,
    errorResponse?: FastApiHttpErrorDto,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.errorResponse = errorResponse;
    this.requestId = requestId || errorResponse?.request_id;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * HTTP 422 - FastAPI Pydantic Validation Error
 */
export class ApiValidationError extends ApiError {
  public readonly validationDetails: FastApiValidationErrorDetail[];

  constructor(
    message: string,
    validationDetails: FastApiValidationErrorDetail[] = [],
    errorResponse?: FastApiHttpErrorDto
  ) {
    super(message, 422, errorResponse);
    this.name = 'ApiValidationError';
    this.validationDetails = validationDetails;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * HTTP 500, 502, 503, 504 - Server and Upstream Gateway Failures
 */
export class ApiServerError extends ApiError {
  constructor(message: string, statusCode: number = 500, errorResponse?: FastApiHttpErrorDto) {
    super(message, statusCode, errorResponse);
    this.name = 'ApiServerError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Request Timeout Error (AbortController triggered or 504)
 */
export class ApiTimeoutError extends ApiError {
  public readonly timeoutMs: number;

  constructor(message: string, timeoutMs: number = 15000) {
    super(message, 504);
    this.name = 'ApiTimeoutError';
    this.timeoutMs = timeoutMs;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Malformed Response Error (200 OK but payload does not match schema)
 */
export class ApiMalformedResponseError extends ApiError {
  public readonly rawPayload: unknown;

  constructor(message: string, rawPayload?: unknown) {
    super(message, 502);
    this.name = 'ApiMalformedResponseError';
    this.rawPayload = rawPayload;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Empty Response Error (HTTP 204 or empty content where data was expected)
 */
export class ApiEmptyResponseError extends ApiError {
  constructor(message: string = 'Server returned an unexpected empty response payload.') {
    super(message, 204);
    this.name = 'ApiEmptyResponseError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Factory parser to construct typed ApiErrors from raw fetch responses
 */
export function createApiErrorFromResponse(
  statusCode: number,
  rawBody: unknown,
  fallbackMessage: string = 'Prescription inference API request failed.'
): ApiError {
  if (!rawBody || typeof rawBody !== 'object') {
    if (statusCode >= 500) {
      return new ApiServerError(`Server error (${statusCode}): ${fallbackMessage}`, statusCode);
    }
    return new ApiError(`API error (${statusCode}): ${fallbackMessage}`, statusCode);
  }

  const errorObj = rawBody as Record<string, unknown>;
  const detail = errorObj.detail;
  const requestId = typeof errorObj.request_id === 'string' ? errorObj.request_id : undefined;

  // Check for FastAPI 422 validation error
  if (statusCode === 422 && Array.isArray(detail)) {
    const validationDetails = detail as FastApiValidationErrorDetail[];
    const firstMsg = validationDetails[0]?.msg || 'Unprocessable Entity';
    const loc = validationDetails[0]?.loc?.join('.') || 'body';
    return new ApiValidationError(
      `Prescription validation failed on ${loc}: ${firstMsg}`,
      validationDetails,
      rawBody as FastApiHttpErrorDto
    );
  }

  const messageText = typeof detail === 'string' ? detail : fallbackMessage;

  if (statusCode === 504) {
    return new ApiTimeoutError(messageText, 15000);
  }

  if (statusCode >= 500) {
    return new ApiServerError(messageText, statusCode, rawBody as FastApiHttpErrorDto);
  }

  return new ApiError(messageText, statusCode, rawBody as FastApiHttpErrorDto, requestId);
}
