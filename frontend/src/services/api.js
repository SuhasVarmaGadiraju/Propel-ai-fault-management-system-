import axios from 'axios';

/**
 * Production-ready Axios HTTP client configuration
 */
let envBaseUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

if (typeof envBaseUrl === 'string') {
  envBaseUrl = envBaseUrl.trim();
  // Strip accidental variable name prefix if full key=value line was set in env configuration
  if (envBaseUrl.startsWith('VITE_API_BASE_URL=')) {
    envBaseUrl = envBaseUrl.replace(/^VITE_API_BASE_URL=/, '').trim();
  }
  if (envBaseUrl.startsWith('VITE_API_URL=')) {
    envBaseUrl = envBaseUrl.replace(/^VITE_API_URL=/, '').trim();
  }
  // Strip enclosing quotes if present
  envBaseUrl = envBaseUrl.replace(/^["']|["']$/g, '');
}

const apiClient = axios.create({
  baseURL: envBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Inject auth token or custom headers here in future phases
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Standardize client error handling
    const customError = {
      message: error.response?.data?.error?.description || 'An unexpected error occurred',
      status: error.response?.status || 500,
    };
    return Promise.reject(customError);
  }
);

export default apiClient;
