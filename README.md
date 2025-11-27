# 🌙 Lyra AI Mark2

**Lightweight offline + cloud hybrid AI desktop assistant**

Lyra is a cross-platform AI assistant that runs on Windows, macOS, and Linux with support for:
- 💬 Text chat interface
- 🎙️ Real-time voice interaction (STT → LLM → TTS)
- 👁️ Vision features (OCR + object detection)
- 📝 Reminders and system tools
- 🔄 Intelligent model routing (offline/hybrid/cloud)
- ⚡ Extremely low resource usage

## 🏗️ Architecture

```
Lyra-Mark2/
├── ai-worker/          # Python FastAPI backend
│   ├── app.py          # Main server
│   ├── model_router.py # Intelligent model selection
│   ├── stt.py          # Speech-to-text (Vosk)
│   ├── tts.py          # Text-to-speech (pyttsx3)
│   ├── vision.py       # OCR + object detection
│   ├── tools/          # System tools
│   │   ├── reminders.py
│   │   ├── clipboard.py
│   │   └── system_control.py
│   ├── memory/         # Vector memory
│   │   └── vector_store.py
│   └── models/         # GGUF models (not included)
└── ui/                 # Tauri + React frontend
    ├── src/
    │   ├── App.tsx
    │   ├── components/
    │   └── hooks/
    └── src-tauri/      # Tauri Rust backend
```

## 🚀 Quick Start

### Prerequisites

**Backend:**
- Python 3.9+
- Tesseract OCR (optional, for vision features)

**Frontend:**
- Node.js 18+
- Rust 1.70+ (for Tauri)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd ai-worker

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The backend will start on `http://localhost:8000`

Visit `http://localhost:8000/docs` for API documentation

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd ui

# Install dependencies
npm install

# Run in development mode
npm run tauri:dev

# Or build for production
npm run tauri:build
```

## 🤖 Model Configuration

### Model Modes

Lyra supports four model modes:

1. **Offline Mini** (Default)
   - Uses lightweight local models (1-3B parameters)
   - RAM requirement: 4-8 GB
   - Best for: Low-end systems, privacy-focused users

2. **Offline Big**
   - Uses larger local models (7-13B parameters)
   - RAM requirement: 16-32 GB
   - Best for: High-end systems, maximum quality

3. **Hybrid** (Recommended)
   - Tries local models first, falls back to cloud
   - Balances privacy, cost, and quality
   - Best for: Most users

4. **Cloud Only**
   - Always uses cloud APIs (Gemini/OpenAI)
   - Requires API keys and internet
   - Best for: Maximum quality, no local resources

### Installing Local Models

1. Download GGUF models from [Hugging Face](https://huggingface.co/models?library=gguf)

**Recommended models:**
- **Mini:** [TinyLlama-1.1B](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
- **Big:** [Mistral-7B](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)

2. Place models in `ai-worker/models/`

```
ai-worker/models/
├── tinyllama-1.1b.gguf    # Mini model
└── mistral-7b.gguf        # Big model
```

3. Restart the backend

The model router will automatically detect and use available models.

### Cloud API Setup (Optional)

To use cloud mode, set environment variables:

```bash
# For Gemini
export GOOGLE_API_KEY="your-api-key"

# For OpenAI
export OPENAI_API_KEY="your-api-key"
```

## 📡 API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /stt` - Speech-to-text
- `POST /tts` - Text-to-speech
- `POST /vision/frame` - Analyze image frame
- `POST /llm/query` - Query LLM

### WebSocket

- `WS /realtime` - Real-time voice interaction

## 🎨 Features

### Chat Interface
- ChatGPT-style conversation
- Message history
- Typing indicators
- Auto-scroll

### Realtime Voice
- Push-to-talk interaction
- Live transcription
- Audio playback
- Waveform visualization

### Vision
- OCR text extraction (pytesseract)
- Object detection (ready for YOLOv8)
- Face detection (OpenCV)

### Tools
- Reminders with JSON persistence
- Clipboard operations
- System control (open apps, URLs)

### Memory
- Vector-based semantic memory
- FAISS + sentence-transformers
- Context-aware responses

## 🔧 Development

### Backend Development

```bash
cd ai-worker

# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
python app.py
```

### Frontend Development

```bash
cd ui

# Run dev server
npm run dev

# Run Tauri dev mode
npm run tauri:dev

# Type checking
npm run tsc
```

## 🐛 Troubleshooting

### Backend Issues

**Vosk not working:**
- Download Vosk model from https://alphacephei.com/vosk/models
- Extract to `ai-worker/models/vosk-model-small-en-us/`

**Tesseract not found:**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

**pyttsx3 not working:**
- Windows: Should work out of the box
- macOS: `brew install espeak`
- Linux: `sudo apt-get install espeak`

### Frontend Issues

**Tauri build fails:**
- Ensure Rust is installed: https://rustup.rs/
- Update Rust: `rustup update`

**WebSocket connection fails:**
- Ensure backend is running on port 8000
- Check firewall settings

## 📦 Building for Production

### Backend

```bash
cd ai-worker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

### Frontend

```bash
cd ui

# Build Tauri app
npm run tauri:build
```

Installers will be in `ui/src-tauri/target/release/bundle/`

## 🔒 Privacy & Security

- **Offline by default:** All processing happens locally
- **No telemetry:** Zero data collection
- **Cloud optional:** You control when to use cloud APIs
- **Open source:** Fully auditable code

## 🛣️ Roadmap

- [ ] Mobile apps (Android, iOS)
- [ ] Plugin system
- [ ] Custom wake word
- [ ] Screen sharing analysis
- [ ] Multi-language support
- [ ] Voice cloning
- [ ] Advanced automation

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 💬 Support

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas

---

**Built with ❤️ for privacy-conscious AI enthusiasts**
