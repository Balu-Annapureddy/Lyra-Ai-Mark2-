import { AppState, ModelMode } from "../App";

interface SettingsPanelProps {
    appState: AppState;
    onUpdateSettings: (updates: Partial<AppState>) => void;
}

export default function SettingsPanel({
    appState,
    onUpdateSettings,
}: SettingsPanelProps) {
    const modelModes: { value: ModelMode; label: string; description: string }[] =
        [
            {
                value: "offline-mini",
                label: "Offline Mini",
                description: "Lightweight local model (1-3B params, 4-8GB RAM)",
            },
            {
                value: "offline-big",
                label: "Offline Big",
                description: "Larger local model (7-13B params, 16-32GB RAM)",
            },
            {
                value: "hybrid",
                label: "Hybrid (Recommended)",
                description: "Local when available, cloud fallback",
            },
            {
                value: "cloud",
                label: "Cloud Only",
                description: "Always use cloud APIs (Gemini/OpenAI)",
            },
        ];

    return (
        <div className="settings-panel">
            <h2>⚙️ Settings</h2>

            <div className="settings-section">
                <h3>🤖 Model Mode</h3>
                <p className="section-description">
                    Choose how Lyra processes your requests
                </p>

                <div className="model-modes">
                    {modelModes.map((modeOption) => (
                        <div
                            key={modeOption.value}
                            className={`mode-option ${appState.mode === modeOption.value ? "selected" : ""
                                }`}
                            onClick={() => onUpdateSettings({ mode: modeOption.value })}
                        >
                            <div className="mode-header">
                                <input
                                    type="radio"
                                    name="model-mode"
                                    checked={appState.mode === modeOption.value}
                                    onChange={() => onUpdateSettings({ mode: modeOption.value })}
                                />
                                <label>{modeOption.label}</label>
                            </div>
                            <p className="mode-description">{modeOption.description}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="settings-section">
                <h3>🎙️ Audio & Video</h3>

                <div className="setting-item">
                    <label>
                        <input
                            type="checkbox"
                            checked={appState.micEnabled}
                            onChange={(e) =>
                                onUpdateSettings({ micEnabled: e.target.checked })
                            }
                        />
                        Enable Microphone
                    </label>
                    <p className="setting-description">
                        Allow Lyra to listen to your voice
                    </p>
                </div>

                <div className="setting-item">
                    <label>
                        <input
                            type="checkbox"
                            checked={appState.cameraEnabled}
                            onChange={(e) =>
                                onUpdateSettings({ cameraEnabled: e.target.checked })
                            }
                        />
                        Enable Camera
                    </label>
                    <p className="setting-description">
                        Allow Lyra to see and analyze images (OCR, object detection)
                    </p>
                </div>
            </div>

            <div className="settings-section">
                <h3>🎨 Appearance</h3>

                <div className="setting-item">
                    <label>
                        Theme:
                        <select
                            value={appState.theme}
                            onChange={(e) =>
                                onUpdateSettings({
                                    theme: e.target.value as "light" | "dark",
                                })
                            }
                        >
                            <option value="dark">Dark</option>
                            <option value="light">Light</option>
                        </select>
                    </label>
                </div>
            </div>

            <div className="settings-section">
                <h3>ℹ️ System Information</h3>
                <div className="system-info">
                    <div className="info-item">
                        <span className="info-label">Backend Status:</span>
                        <span
                            className={`info-value ${appState.isConnected ? "connected" : "disconnected"
                                }`}
                        >
                            {appState.isConnected ? "Connected" : "Disconnected"}
                        </span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Current Mode:</span>
                        <span className="info-value">{appState.mode}</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Version:</span>
                        <span className="info-value">1.0.0</span>
                    </div>
                </div>
            </div>

            <div className="settings-section">
                <h3>📚 Quick Guide</h3>
                <div className="quick-guide">
                    <h4>Getting Started:</h4>
                    <ol>
                        <li>Start the backend server: <code>python ai-worker/app.py</code></li>
                        <li>Choose your preferred model mode above</li>
                        <li>Enable microphone for voice interaction</li>
                        <li>Start chatting or use realtime mode!</li>
                    </ol>

                    <h4>Model Setup:</h4>
                    <ul>
                        <li>
                            Download GGUF models from{" "}
                            <a
                                href="https://huggingface.co/models?library=gguf"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Hugging Face
                            </a>
                        </li>
                        <li>Place models in <code>ai-worker/models/</code></li>
                        <li>Restart backend to detect new models</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
