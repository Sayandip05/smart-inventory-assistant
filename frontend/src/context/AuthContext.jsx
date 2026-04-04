/**
 * AuthContext — Global authentication state for Smart Inventory Assistant.
 *
 * Provides:
 * - Login / logout functions
 * - Current user object decoded from JWT
 * - Token storage in localStorage
 * - Token refresh handling (automatic on 401)
 * - Role-based helpers (isAdmin, isManager, etc.)
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api, { auth } from '../services/api';

const AuthContext = createContext(null);

/** Decode JWT payload without a library (tokens are base64 encoded, not encrypted). */
function decodeJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const json = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(json);
    } catch {
        return null;
    }
}

/** Check if token is expired or will expire within buffer (seconds) */
function isTokenExpired(token, bufferSeconds = 60) {
    const payload = decodeJwt(token);
    if (!payload || !payload.exp) return true;
    return payload.exp * 1000 < Date.now() + bufferSeconds * 1000;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const isRefreshing = useRef(false);
    const refreshSubscribers = useRef([]);

    // ── Restore session on first load ──────────────────────────────────────
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            const payload = decodeJwt(token);
            if (payload && payload.exp * 1000 > Date.now()) {
                setUser({
                    id: payload.sub,
                    username: payload.username,
                    role: payload.role,
                });
            } else {
                // Token expired — try to refresh
                refreshAccessToken().then((newToken) => {
                    if (!newToken) {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                    }
                });
            }
        }
        setLoading(false);
    }, []);

    // ── Token Refresh Logic ────────────────────────────────────────────────
    const refreshAccessToken = useCallback(async () => {
        if (isRefreshing.current) {
            // Wait for ongoing refresh
            return new Promise((resolve) => {
                refreshSubscribers.current.push(resolve);
            });
        }

        isRefreshing.current = true;
        const refreshToken = localStorage.getItem('refresh_token');

        if (!refreshToken) {
            isRefreshing.current = false;
            notifySubscribers(null);
            return null;
        }

        try {
            const response = await auth.refresh({ refresh_token: refreshToken });
            const { access_token, refresh_token: newRefreshToken } = response.data.data;

            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', newRefreshToken);

            const payload = decodeJwt(access_token);
            setUser({
                id: payload.sub,
                username: payload.username,
                role: payload.role,
            });

            notifySubscribers(access_token);
            return access_token;
        } catch (error) {
            // Refresh failed — clear everything
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            notifySubscribers(null);
            return null;
        } finally {
            isRefreshing.current = false;
        }
    }, []);

    const notifySubscribers = (token) => {
        refreshSubscribers.current.forEach((callback) => callback(token));
        refreshSubscribers.current = [];
    };

    // ── Setup Axios Interceptor for Token Refresh ──────────────────────────
    useEffect(() => {
        const interceptor = api.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;

                // If 401 and not already retrying
                if (error?.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;

                    const newToken = await refreshAccessToken();
                    if (newToken) {
                        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                        return api(originalRequest);
                    }
                }

                return Promise.reject(error);
            }
        );

        return () => {
            api.interceptors.response.eject(interceptor);
        };
    }, [refreshAccessToken]);

    // ── Login ──────────────────────────────────────────────────────────────
    const login = useCallback(async (username, password) => {
        const response = await api.post('/auth/login', { username, password });
        const { access_token, refresh_token } = response.data.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        const payload = decodeJwt(access_token);
        const userData = {
            id: payload.sub,
            username: payload.username,
            role: payload.role,
        };
        setUser(userData);
        return userData;
    }, []);

    // ── Logout ─────────────────────────────────────────────────────────────
    const logout = useCallback(async () => {
        try {
            await api.post('/auth/logout');
        } catch {
            // Ignore errors — still clear local state
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
        }
    }, []);

    // ── Role helpers ───────────────────────────────────────────────────────
    const isAdmin = user?.role === 'admin';
    const isManager = user?.role === 'manager' || isAdmin;
    const isStaff = user?.role === 'staff' || isManager;

    const value = {
        user,
        loading,
        login,
        logout,
        isAdmin,
        isManager,
        isStaff,
        isAuthenticated: !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Hook to consume auth context anywhere in the app. */
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
}
