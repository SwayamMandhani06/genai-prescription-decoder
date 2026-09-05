import {
  PrescriptionAnalyzeResponseDto,
  PrescriptionAnalyzeOptionsDto,
} from '../../types/api.types';
import { apiConfig } from './apiConfig';
import { defaultApiClient } from './apiClient';
import {
  CONFIDENT_RESPONSE_FIXTURE,
  UNCERTAIN_RESPONSE_FIXTURE,
  FLAGGED_RESPONSE_FIXTURE,
  LASA_WARNING_RESPONSE_FIXTURE,
  FASTAPI_VALIDATION_ERROR_FIXTURE,
  FASTAPI_SERVER_ERROR_FIXTURE,
  FASTAPI_GATEWAY_TIMEOUT_FIXTURE,
} from './prescriptionFixtures';
import {
  ApiValidationError,
  ApiServerError,
  ApiTimeoutError,
  ApiMalformedResponseError,
  ApiEmptyResponseError,
} from './apiErrors';

export interface IPrescriptionApiClient {
  analyzePrescription(
    input: File | string,
    options?: PrescriptionAnalyzeOptionsDto
  ): Promise<PrescriptionAnalyzeResponseDto>;
}

/**
 * 1. MOCK IMPLEMENTATION (Simulated FastAPI Backend)
 * Emulates the exact response shape, network delay, and HTTP errors of FastAPI.
 */
export class MockPrescriptionApiClient implements IPrescriptionApiClient {
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async analyzePrescription(
    input: File | string,
    options: PrescriptionAnalyzeOptionsDto = {}
  ): Promise<PrescriptionAnalyzeResponseDto> {
    const scenario = options.mock_scenario;

    // Simulate realistic network transmission delay
    await this.delay(550);

    // 1. Fault Injection: Validation Error (HTTP 422)
    if (scenario === 'validation_error') {
      throw new ApiValidationError(
        'Document image resolution falls below the minimum required diagnostic threshold (422 Unprocessable Entity).',
        FASTAPI_VALIDATION_ERROR_FIXTURE.detail as any,
        FASTAPI_VALIDATION_ERROR_FIXTURE
      );
    }

    // 2. Fault Injection: Server Error (HTTP 500)
    if (scenario === 'server_error') {
      throw new ApiServerError(
        'Internal GPU Inference Worker Failure: CUDA out-of-memory while executing cross-attention decoder.',
        500,
        FASTAPI_SERVER_ERROR_FIXTURE
      );
    }

    // 3. Fault Injection: Gateway Timeout (HTTP 504)
    if (scenario === 'timeout') {
      throw new ApiTimeoutError(
        typeof FASTAPI_GATEWAY_TIMEOUT_FIXTURE.detail === 'string'
          ? FASTAPI_GATEWAY_TIMEOUT_FIXTURE.detail
          : 'CDSCO Drug Database & RxNorm Formulary Gateway connection timed out after 15,000ms.',
        15000
      );
    }

    // 4. Fault Injection: Malformed Response
    if (scenario === 'malformed') {
      throw new ApiMalformedResponseError(
        'Backend returned 200 OK but payload JSON could not be parsed.',
        '<html><body>502 Bad Gateway: Upstream Nginx Error</body></html>'
      );
    }

    // 5. Fault Injection: Empty Response
    if (scenario === 'empty') {
      throw new ApiEmptyResponseError('Backend returned empty payload (HTTP 204 No Content).');
    }

    // 6. Explicit Scenario Fixtures
    if (scenario === 'confident') return { ...CONFIDENT_RESPONSE_FIXTURE };
    if (scenario === 'uncertain') return { ...UNCERTAIN_RESPONSE_FIXTURE };
    if (scenario === 'flagged') return { ...FLAGGED_RESPONSE_FIXTURE };
    if (scenario === 'lasa_warning') return { ...LASA_WARNING_RESPONSE_FIXTURE };

    // 7. Dynamic Resolution based on sample key or uploaded file
    if (typeof input === 'string') {
      if (input === 'rx-sample-2') return { ...LASA_WARNING_RESPONSE_FIXTURE };
      if (input === 'rx-sample-3') return { ...FLAGGED_RESPONSE_FIXTURE };
      if (input === 'rx-sample-1') return { ...CONFIDENT_RESPONSE_FIXTURE };
    }

    // Default to confident clinical fixture
    return { ...CONFIDENT_RESPONSE_FIXTURE };
  }
}

/**
 * 2. REAL HTTP IMPLEMENTATION (Live FastAPI Backend)
 * Dispatches multipart/form-data to POST /api/v1/prescriptions/analyze
 */
export class HttpPrescriptionApiClient implements IPrescriptionApiClient {
  async analyzePrescription(
    input: File | string,
    options: PrescriptionAnalyzeOptionsDto = {}
  ): Promise<PrescriptionAnalyzeResponseDto> {
    const formData = new FormData();

    if (input instanceof File) {
      formData.append('file', input, input.name);
    } else {
      // If sample key string is provided in demo mode
      formData.append('sample_id', input);
    }

    if (options.confidence_threshold !== undefined) {
      formData.append('confidence_threshold', options.confidence_threshold.toString());
    }

    if (options.enable_lasa_detection !== undefined) {
      formData.append('enable_lasa_detection', options.enable_lasa_detection ? 'true' : 'false');
    }

    if (options.target_language) {
      formData.append('target_language', options.target_language);
    }

    return defaultApiClient.postFormData<PrescriptionAnalyzeResponseDto>(
      apiConfig.endpoints.analyze,
      formData,
      {
        timeoutMs: apiConfig.requestTimeoutMs,
      }
    );
  }
}

/**
 * Client factory dynamically choosing between Mock and Live backend
 */
export function getPrescriptionApiClient(): IPrescriptionApiClient {
  if (apiConfig.useMock) {
    return new MockPrescriptionApiClient();
  }
  return new HttpPrescriptionApiClient();
}
