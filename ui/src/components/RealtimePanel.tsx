import { useState, useEffect, useRef } from "react";
import { ModelMode } from "../App";
import useWebSocket from "../hooks/useWebSocket";
import { WS_BASE_URL } from "../config";

interface RealtimePanelProps {
    mode: ModelMode;
    micEnabled: boolean;
    onMicToggle: (enabled: boolean) => void;
    isConnected: boolean;
}

export default function RealtimePanel({
    mode,
    micEnabled,
    onMicToggle,
    isConnected,
}: RealtimePanelProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [response, setResponse] = useState("");
    const [status, setStatus] = useState("Ready");

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    // WebSocket connection
    const { sendMessage, lastMessage, connectionStatus } = useWebSocket(
        `${WS_BASE_URL}/realtime`
    );

    // Handle incoming WebSocket messages
    useEffect(() => {
        if (lastMessage) {
            const data = JSON.parse(lastMessage);

            switch (data.type) {
                case "transcription":
                    setTranscript(data.text);
                    setStatus("Processing...");
                    break;
                case "llm_response":
                    setResponse(data.text);
                    setStatus("Generating speech...");
                    break;
                case "audio_response":
                    playAudio(data.audio);
                    setStatus("Ready");
                    break;
            }
        }
    }, [lastMessage]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, {
                    type: "audio/wav",
                });
                await sendAudioToBackend(audioBlob);
                stream.getTracks().forEach((track) => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
            setStatus("Listening...");
            onMicToggle(true);
        } catch (error) {
            console.error("Failed to start recording:", error);
            setStatus("Microphone access denied");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setStatus("Processing...");
            onMicToggle(false);
        }
    };

    const sendAudioToBackend = async (audioBlob: Blob) => {
        try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64Audio = (reader.result as string).split(",")[1];
                sendMessage({
                    type: "audio",
                    audio: base64Audio,
                    mode: mode,
                });
            };
            reader.readAsDataURL(audioBlob);
        } catch (error) {
            console.error("Failed to send audio:", error);
            setStatus("Error sending audio");
        }
    };

    const playAudio = (base64Audio: string) => {
        try {
            const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
            audio.play();
        } catch (error) {
            console.error("Failed to play audio:", error);
        }
    };

    return (
        <div className="realtime-panel">
            <div className="realtime-header">
                <h2>🎙️ Realtime Voice Interaction</h2>
                <p className="realtime-description">
                    Press and hold the microphone button to speak, release to send
                </p>
            </div>

            <div className="realtime-status">
                <div className={`status-indicator ${isRecording ? "recording" : ""}`}>
                    {status}
                </div>
                <div className={`connection-status ${connectionStatus}`}>
                    WebSocket: {connectionStatus}
                </div>
            </div>

            <div className="realtime-controls">
                <button
                    className={`mic-button ${isRecording ? "recording" : ""}`}
                    onMouseDown={startRecording}
                    onMouseUp={stopRecording}
                    onTouchStart={startRecording}
                    onTouchEnd={stopRecording}
                    disabled={!isConnected || connectionStatus !== "connected"}
                >
                    <span className="mic-icon">{isRecording ? "🔴" : "🎤"}</span>
                    <span className="mic-label">
                        {isRecording ? "Release to Send" : "Hold to Speak"}
                    </span>
                </button>
            </div>

            {isRecording && (
                <div className="waveform-animation">
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                </div>
            )}

            <div className="realtime-output">
                {transcript && (
                    <div className="output-section">
                        <h3>📝 You said:</h3>
                        <p className="transcript">{transcript}</p>
                    </div>
                )}

                {response && (
                    <div className="output-section">
                        <h3>🌙 Lyra responded:</h3>
                        <p className="response">{response}</p>
                    </div>
                )}
            </div>

            <div className="realtime-tips">
                <h4>💡 Tips:</h4>
                <ul>
                    <li>Make sure your microphone is enabled in browser settings</li>
                    <li>Speak clearly and wait for the response</li>
                    <li>Use Push-to-Talk for better control</li>
                    <li>Switch to Chat mode for text-only interaction</li>
                </ul>
            </div>
        </div>
    );
}
