import { AppState } from "../App";

interface TopBarProps {
    appState: AppState;
    onPanelChange: (panel: "chat" | "realtime" | "settings") => void;
    onThemeToggle: () => void;
}

export default function TopBar({
    appState,
    onPanelChange,
    onThemeToggle,
}: TopBarProps) {
    return (
        <header className="top-bar">
            <div className="top-bar-left">
                <h1 className="app-title">🌙 Lyra AI</h1>
                <span className="connection-status">
                    {appState.isConnected ? (
                        <span className="status-connected">● Connected</span>
                    ) : (
                        <span className="status-disconnected">● Disconnected</span>
                    )}
                </span>
            </div>

            <nav className="top-bar-nav">
                <button
                    className={`nav-button ${appState.currentPanel === "chat" ? "active" : ""
                        }`}
                    onClick={() => onPanelChange("chat")}
                >
                    💬 Chat
                </button>
                <button
                    className={`nav-button ${appState.currentPanel === "realtime" ? "active" : ""
                        }`}
                    onClick={() => onPanelChange("realtime")}
                >
                    🎙️ Realtime
                </button>
                <button
                    className={`nav-button ${appState.currentPanel === "settings" ? "active" : ""
                        }`}
                    onClick={() => onPanelChange("settings")}
                >
                    ⚙️ Settings
                </button>
            </nav>

            <div className="top-bar-right">
                <button className="theme-toggle" onClick={onThemeToggle}>
                    {appState.theme === "dark" ? "☀️" : "🌙"}
                </button>
            </div>
        </header>
    );
}
