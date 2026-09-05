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
    health: string;
  };
}

export const apiConfig: ApiConfiguration = {
  // Configured to point to future FastAPI server; default http://localhost:8000
  baseUrl: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000',
  // Defaults to mock adapter unless VITE_USE_MOCK_API is set to 'false'
  useMock: import.meta.env.VITE_USE_MOCK_API !== 'false',
  requestTimeoutMs: 15000,
  endpoints: {
    analyze: '/api/v1/prescriptions/analyze',
    health: '/api/v1/health',
  },
};

/**
 * Runtime switcher for academic demos and automated integration tests
 */
export function setApiMockMode(enableMock: boolean): void {
  apiConfig.useMock = enableMock;
}
