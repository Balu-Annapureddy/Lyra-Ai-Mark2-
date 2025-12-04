import { useState, useRef, useEffect } from "react";
import { ModelMode } from "../App";
import { API_BASE_URL } from "../config";

interface Message {
    id: number;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

interface ChatPanelProps {
    mode: ModelMode;
    isConnected: boolean;
}

export default function ChatPanel({ mode, isConnected }: ChatPanelProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 1,
            role: "assistant",
            content: "Hello! I'm Lyra, your AI assistant. How can I help you today?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || !isConnected) return;

        const userMessage: Message = {
            id: messages.length + 1,
            role: "user",
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            // Send to backend
            const response = await fetch(`${API_BASE_URL}/llm/query`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    query: input,
                    mode: mode,
                }),
            });

            const data = await response.json();

            const assistantMessage: Message = {
                id: messages.length + 2,
                role: "assistant",
                content: data.response,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Failed to send message:", error);
            const errorMessage: Message = {
                id: messages.length + 2,
                role: "assistant",
                content: "Sorry, I encountered an error. Please try again.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="chat-panel">
            <div className="messages-container">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.role}`}>
                        <div className="message-avatar">
                            {message.role === "user" ? "👤" : "🌙"}
                        </div>
                        <div className="message-content">
                            <div className="message-text">{message.content}</div>
                            <div className="message-time">
                                {message.timestamp.toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-avatar">🌙</div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    className="message-input"
                    placeholder={
                        isConnected
                            ? "Type your message... (Enter to send, Shift+Enter for new line)"
                            : "Connect to backend to start chatting..."
                    }
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={!isConnected}
                    rows={3}
                />
                <button
                    className="send-button"
                    onClick={sendMessage}
                    disabled={!isConnected || !input.trim() || isLoading}
                >
                    {isLoading ? "⏳" : "📤"} Send
                </button>
            </div>
        </div>
    );
}
