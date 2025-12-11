/**
 * Sprint 26: Authentication Context
 * 
 * Manages authentication state and tokens
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { useRouter, useSegments } from 'expo-router';
import { api } from '@/services/api';

interface User {
    id: string;
    name: string;
    email: string;
    cpf?: string;
    avatar?: string;
    patientId?: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'openehrcore_access_token';
const REFRESH_TOKEN_KEY = 'openehrcore_refresh_token';
const USER_KEY = 'openehrcore_user';

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const segments = useSegments();

    // Check authentication on mount
    useEffect(() => {
        checkAuth();
    }, []);

    // Redirect based on auth state
    useEffect(() => {
        if (isLoading) return;

        const inAuthGroup = segments[0] === '(auth)';

        if (!user && !inAuthGroup) {
            // Redirect to login
            router.replace('/(auth)/login');
        } else if (user && inAuthGroup) {
            // Redirect to main app
            router.replace('/(tabs)');
        }
    }, [user, segments, isLoading]);

    const checkAuth = async () => {
        try {
            const token = await SecureStore.getItemAsync(TOKEN_KEY);
            const userJson = await SecureStore.getItemAsync(USER_KEY);

            if (token && userJson) {
                setUser(JSON.parse(userJson));
                api.setAuthToken(token);
            }
        } catch (error) {
            console.error('Error checking auth:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        try {
            setIsLoading(true);

            // Call auth API
            const response = await api.post('/auth/login', { email, password });
            const { access_token, refresh_token, user: userData } = response.data;

            // Store tokens securely
            await SecureStore.setItemAsync(TOKEN_KEY, access_token);
            await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);
            await SecureStore.setItemAsync(USER_KEY, JSON.stringify(userData));

            // Update state
            api.setAuthToken(access_token);
            setUser(userData);
        } catch (error: any) {
            throw new Error(error.response?.data?.message || 'Erro ao fazer login');
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        try {
            // Clear stored data
            await SecureStore.deleteItemAsync(TOKEN_KEY);
            await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
            await SecureStore.deleteItemAsync(USER_KEY);

            // Clear state
            api.setAuthToken(null);
            setUser(null);
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    const refreshToken = async () => {
        try {
            const storedRefreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
            if (!storedRefreshToken) {
                throw new Error('No refresh token');
            }

            const response = await api.post('/auth/refresh', {
                refresh_token: storedRefreshToken,
            });

            const { access_token, refresh_token: newRefreshToken } = response.data;

            await SecureStore.setItemAsync(TOKEN_KEY, access_token);
            await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, newRefreshToken);

            api.setAuthToken(access_token);
        } catch (error) {
            // If refresh fails, logout
            await logout();
            throw error;
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                logout,
                refreshToken,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
