import { useEffect, useRef, useState } from "react";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface UseWebSocketReturn {
    sendMessage: (data: any) => void;
    lastMessage: string | null;
    connectionStatus: ConnectionStatus;
}

export default function useWebSocket(url: string): UseWebSocketReturn {
    const [connectionStatus, setConnectionStatus] =
        useState<ConnectionStatus>("disconnected");
    const [lastMessage, setLastMessage] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [url]);

    const connect = () => {
        try {
            setConnectionStatus("connecting");
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("WebSocket connected");
                setConnectionStatus("connected");

                // Start heartbeat
                startHeartbeat();
            };

            ws.onmessage = (event) => {
                setLastMessage(event.data);
            };

            ws.onerror = (error) => {
                console.error("WebSocket error:", error);
                setConnectionStatus("disconnected");
            };

            ws.onclose = () => {
                console.log("WebSocket disconnected");
                setConnectionStatus("disconnected");

                // Attempt reconnection after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log("Attempting to reconnect...");
                    connect();
                }, 3000);
            };
        } catch (error) {
            console.error("Failed to connect WebSocket:", error);
            setConnectionStatus("disconnected");
        }
    };

    const disconnect = () => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    const startHeartbeat = () => {
        const interval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                sendMessage({ type: "ping" });
            } else {
                clearInterval(interval);
            }
        }, 30000); // Ping every 30 seconds
    };

    const sendMessage = (data: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        } else {
            console.error("WebSocket is not connected");
        }
    };

    return {
        sendMessage,
        lastMessage,
        connectionStatus,
    };
}
