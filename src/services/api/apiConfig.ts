/**
 * API Client Configuration
 * Allows zero-code toggle between Mock Fixtures Adapter and Live FastAPI Backend.
 */

export interface ApiConfiguration {
  baseUrl: string;
  useMock: boolean;
  requestTimeoutMs: number;
  endpoints: {
    analyze: string;
    process: string;
    health: string;
  };
}

const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL as string)?.trim() || 'http://127.0.0.1:8001';
const isMockExplicitlyDisabled =
  import.meta.env.VITE_USE_MOCK_API === 'false' || import.meta.env.VITE_USE_MOCK_API === '0';

export const apiConfig: ApiConfiguration = {
  // Configured to point to FastAPI server; trims any accidental trailing slashes
  baseUrl: rawBaseUrl.replace(/\/+$/, ''),
  // Defaults to mock adapter unless VITE_USE_MOCK_API is explicitly set to 'false'
  useMock: !isMockExplicitlyDisabled,
  requestTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 60000,
  endpoints: {
    analyze: '/api/v1/prescriptions/analyze',
    process: '/api/v1/prescriptions/process',
    health: '/api/v1/health',
  },
};

/**
 * Runtime switcher for academic demos and automated integration tests
 */
export function setApiMockMode(enableMock: boolean): void {
  apiConfig.useMock = enableMock;
}
