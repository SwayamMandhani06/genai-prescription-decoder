import { apiConfig } from './apiConfig';
import {
  ApiError,
  ApiTimeoutError,
  ApiEmptyResponseError,
  ApiMalformedResponseError,
  createApiErrorFromResponse,
} from './apiErrors';

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  params?: Record<string, string>;
}

export class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string = apiConfig.baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /**
   * Generic request executor with timeout and normalized error parsing
   */
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { timeoutMs = apiConfig.requestTimeoutMs, params, ...customInit } = options;

    let url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

    if (params) {
      const searchParams = new URLSearchParams(params);
      url += (url.includes('?') ? '&' : '?') + searchParams.toString();
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    try {
      const response = await fetch(url, {
        ...customInit,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...customInit.headers,
        },
      });

      clearTimeout(timeoutId);

      // Handle HTTP 204 No Content
      if (response.status === 204) {
        return null as unknown as T;
      }

      // Read response body as text first to handle empty or non-JSON payloads safely
      const responseText = await response.text();

      if (!responseText || responseText.trim() === '') {
        if (response.ok) {
          throw new ApiEmptyResponseError();
        }
        throw new ApiError(`HTTP Error (${response.status}) with empty response body.`, response.status);
      }

      let parsedJson: unknown;
      try {
        parsedJson = JSON.parse(responseText);
      } catch (jsonErr) {
        if (response.ok) {
          throw new ApiMalformedResponseError(
            'Server returned 200 OK but response body could not be parsed as JSON.',
            responseText
          );
        }
        throw new ApiError(
          `Server returned status ${response.status} with non-JSON body: ${responseText.slice(0, 120)}`,
          response.status
        );
      }

      if (!response.ok) {
        throw createApiErrorFromResponse(response.status, parsedJson);
      }

      return parsedJson as T;
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (err instanceof ApiError) {
        throw err;
      }

      // Handle DOMException from AbortController
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiTimeoutError(
          `API request to ${endpoint} timed out after ${timeoutMs}ms.`,
          timeoutMs
        );
      }

      if (err instanceof TypeError && err.message.includes('fetch')) {
        throw new ApiError(
          `Network connection failed: Unable to reach FastAPI backend at ${this.baseUrl}. Verify that the server is online.`,
          0
        );
      }

      throw new ApiError(
        err instanceof Error ? err.message : 'Unknown API transport error occurred.',
        500
      );
    }
  }

  /**
   * Helper for multipart/form-data upload (e.g. POST /api/v1/prescriptions/analyze)
   */
  async postFormData<T>(endpoint: string, formData: FormData, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      ...options,
    });
  }

  /**
   * Helper for JSON POST
   */
  async postJson<T>(endpoint: string, data: unknown, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  }
}

export const defaultApiClient = new ApiClient();
