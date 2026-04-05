import { useEffect, useState, createContext, useContext } from 'react';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
    const [alerts, setAlerts] = useState([]);
    const { user } = useAuth();

    useEffect(() => {
        if (!user) return;

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/alerts`;
        
        let ws;
        let reconnectTimeout;

        const connect = () => {
            try {
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    console.log('WebSocket connected for alerts');
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'low_stock_alert') {
                            setAlerts(prev => [data, ...prev].slice(0, 10));
                        }
                    } catch (err) {
                        console.error('Failed to parse WebSocket message', err);
                    }
                };

                ws.onclose = () => {
                    reconnectTimeout = setTimeout(connect, 3000);
                };

                ws.onerror = (err) => {
                    console.error('WebSocket error', err);
                };
            } catch (err) {
                console.error('Failed to connect WebSocket', err);
            }
        };

        connect();

        return () => {
            if (ws) ws.close();
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
        };
    }, [user]);

    const clearAlert = (index) => {
        setAlerts(prev => prev.filter((_, i) => i !== index));
    };

    const clearAllAlerts = () => {
        setAlerts([]);
    };

    return (
        <WebSocketContext.Provider value={{ alerts, clearAlert, clearAllAlerts }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSocketAlerts() {
    const context = useContext(WebSocketContext);
    if (!context) {
        return { alerts: [], clearAlert: () => {}, clearAllAlerts: () => {} };
    }
    return context;
}