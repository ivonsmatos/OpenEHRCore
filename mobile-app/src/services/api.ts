/**
 * Sprint 26: API Service
 * 
 * Axios instance configured for the mobile app
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000/api/v1';

class ApiService {
    private instance: AxiosInstance;
    private authToken: string | null = null;

    constructor() {
        this.instance = axios.create({
            baseURL: API_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor for auth token
        this.instance.interceptors.request.use(
            (config: InternalAxiosRequestConfig) => {
                if (this.authToken) {
                    config.headers.Authorization = `Bearer ${this.authToken}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor for error handling
        this.instance.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                if (error.response?.status === 401) {
                    // Token expired, try to refresh
                    try {
                        await this.refreshToken();
                        // Retry the original request
                        const config = error.config;
                        if (config) {
                            config.headers.Authorization = `Bearer ${this.authToken}`;
                            return this.instance.request(config);
                        }
                    } catch (refreshError) {
                        // Refresh failed, logout user
                        await SecureStore.deleteItemAsync('openehrcore_access_token');
                        await SecureStore.deleteItemAsync('openehrcore_refresh_token');
                    }
                }
                return Promise.reject(error);
            }
        );
    }

    setAuthToken(token: string | null) {
        this.authToken = token;
    }

    private async refreshToken() {
        const refreshToken = await SecureStore.getItemAsync('openehrcore_refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token');
        }

        const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;

        await SecureStore.setItemAsync('openehrcore_access_token', access_token);
        await SecureStore.setItemAsync('openehrcore_refresh_token', refresh_token);

        this.authToken = access_token;
    }

    // HTTP methods
    get<T>(url: string, config?: object) {
        return this.instance.get<T>(url, config);
    }

    post<T>(url: string, data?: object, config?: object) {
        return this.instance.post<T>(url, data, config);
    }

    put<T>(url: string, data?: object, config?: object) {
        return this.instance.put<T>(url, data, config);
    }

    patch<T>(url: string, data?: object, config?: object) {
        return this.instance.patch<T>(url, data, config);
    }

    delete<T>(url: string, config?: object) {
        return this.instance.delete<T>(url, config);
    }
}

export const api = new ApiService();
export default api;
