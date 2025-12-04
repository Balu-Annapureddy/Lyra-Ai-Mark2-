import { useState, useEffect } from "react";
import TopBar from "./components/TopBar";
import ChatPanel from "./components/ChatPanel";
import RealtimePanel from "./components/RealtimePanel";
import SettingsPanel from "./components/SettingsPanel";
import { API_BASE_URL } from "./config";

export type ModelMode = "offline-mini" | "offline-big" | "hybrid" | "cloud";

export interface AppState {
    mode: ModelMode;
    micEnabled: boolean;
    cameraEnabled: boolean;
    isConnected: boolean;
    currentPanel: "chat" | "realtime" | "settings";
    theme: "light" | "dark";
}

function App() {
    const [appState, setAppState] = useState<AppState>({
        mode: "hybrid",
        micEnabled: false,
        cameraEnabled: false,
        isConnected: false,
        currentPanel: "chat",
        theme: "dark",
    });

    // Check backend connection on mount
    useEffect(() => {
        checkBackendConnection();
    }, []);

    const checkBackendConnection = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                setAppState((prev) => ({ ...prev, isConnected: true }));
            }
        } catch (error) {
            console.error("Backend not connected:", error);
            setAppState((prev) => ({ ...prev, isConnected: false }));
        }
    };

    const updateState = (updates: Partial<AppState>) => {
        setAppState((prev) => ({ ...prev, ...updates }));
    };

    return (
        <div className={`app ${appState.theme}`}>
            <TopBar
                appState={appState}
                onPanelChange={(panel) => updateState({ currentPanel: panel })}
                onThemeToggle={() =>
                    updateState({ theme: appState.theme === "dark" ? "light" : "dark" })
                }
            />

            <main className="app-main">
                {appState.currentPanel === "chat" && (
                    <ChatPanel mode={appState.mode} isConnected={appState.isConnected} />
                )}

                {appState.currentPanel === "realtime" && (
                    <RealtimePanel
                        mode={appState.mode}
                        micEnabled={appState.micEnabled}
                        onMicToggle={(enabled) => updateState({ micEnabled: enabled })}
                        isConnected={appState.isConnected}
                    />
                )}

                {appState.currentPanel === "settings" && (
                    <SettingsPanel
                        appState={appState}
                        onUpdateSettings={(updates) => updateState(updates)}
                    />
                )}
            </main>

            {!appState.isConnected && (
                <div className="connection-warning">
                    ⚠️ Backend not connected. Please start the backend server.
                </div>
            )}
        </div>
    );
}

export default App;
