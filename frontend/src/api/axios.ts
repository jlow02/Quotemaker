declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { getAuthState, getRefreshToken } from '../store/authStore';

const BASE_URL = (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000';

/**
 * @purpose Axios instance for all API calls. Reads JWT from the shared authStore,
 *          handles 401s with a single refresh attempt, redirects to /login on auth failure.
 * @owner [Claude]
 */
const axiosInstance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

let isRefreshing = false;
let failedRequestsQueue: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (callback: (token: string) => void): void => {
  failedRequestsQueue.push(callback);
};

const onRefreshed = (token: string): void => {
  failedRequestsQueue.forEach(cb => cb(token));
  failedRequestsQueue = [];
};

// ── Request interceptor: attach Bearer token ─────────────────────────────
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const { accessToken } = getAuthState();
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// ── Response interceptor: refresh on 401 ─────────────────────────────────
axiosInstance.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => response,
  async (error: AxiosError): Promise<AxiosResponse> => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        getAuthState().clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const resp = await axios.post<{ access_token: string; refresh_token?: string }>(
            `${BASE_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken }
          );
          const newToken = resp.data.access_token;
          getAuthState().setAccessToken(newToken);
          if (resp.data.refresh_token) {
            localStorage.setItem('refreshToken', resp.data.refresh_token);
          }
          isRefreshing = false;
          onRefreshed(newToken);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return axiosInstance(originalRequest);
        } catch {
          isRefreshing = false;
          getAuthState().clearAuth();
          window.location.href = '/login';
          return Promise.reject(error);
        }
      } else {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(axiosInstance(originalRequest));
          });
        });
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
