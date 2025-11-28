# Lyra AI Mark2

Advanced AI assistant with local-first architecture, configurable performance modes, and comprehensive permission system.

## Features

- 🧠 **Local-First AI**: Run models locally for privacy and offline capability
- 🔐 **Permission System**: Fine-grained RBAC for sensitive operations
- 📊 **Model Registry**: RAM-aware model management with compatibility checking
- 💾 **Memory Watchdog**: Automatic RAM monitoring and protection
- ⚡ **Performance Modes**: Configurable modes for different system capabilities
- 🔄 **Event System**: Real-time notifications for permission and system changes
- 📝 **Structured Logging**: JSON-formatted logs for easy analysis
- 🏥 **Health Monitoring**: Comprehensive health checks for all components

## Quick Start

### Prerequisites

- Python 3.10+
- 4GB+ RAM (8GB+ recommended)
- Windows/Linux/macOS

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Lyra-Mark2.git
cd Lyra-Mark2

# Set up virtual environment
cd ai-worker
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Backend

```bash
# From ai-worker directory with venv activated
python app.py
```

The backend will start on `http://localhost:8000`

## Architecture

### Phase 0: Foundation ✅
- Configuration versioning & migration
- Dependency injection container
- Unified error system
- Fail-safe recovery boot

### Phase 1: Configuration & Core Systems ✅
- Configurable memory watchdog
- Permission manager (RBAC)
- Model registry with RAM filtering
- **Enhancements:**
  - Config validation with defaults
  - Permission event system
  - Extended model metadata
  - Registry caching
  - Structured logging
  - Dry-run mode
  - Backup/restore
  - Health check aggregation

### Phase 2: Performance & Stability (In Progress)
- Performance modes (Safe/Balanced)
- Backend stability improvements
- Manager health checks
- Crash recovery system

## Configuration

All configuration files are in `ai-worker/config/`:

- `memory_watchdog.yaml` - RAM monitoring settings
- `model_registry.yaml` - Available models catalog
- `permissions.json` - User permissions
- `performance_modes.yaml` - Performance profiles

## Testing

```bash
# Run Phase 0 tests
python test_phase0.py

# Run Phase 1 tests
python test_phase1.py

# Run Phase 1 enhancement tests
python test_phase1_enhancements.py
```

## Project Structure

```
Lyra-Mark2/
├── ai-worker/              # Backend application
│   ├── api/                # API routes
│   ├── config/             # Configuration files
│   ├── core/               # Core managers and systems
│   │   ├── managers/       # Manager classes
│   │   ├── events.py       # Event bus
│   │   ├── container.py    # DI container
│   │   └── ...
│   ├── error/              # Error handling
│   ├── skills/             # AI skills/capabilities
│   ├── tools/              # Tool implementations
│   └── app.py              # Main application
├── ui/                     # Frontend (Tauri + React)
└── README.md
```

## API Endpoints

- `GET /health` - Basic health check
- `GET /health/core` - Detailed component health
- `GET /models` - List available models
- `GET /permissions` - Get permission status
- `POST /permissions/{name}/grant` - Grant permission
- `POST /permissions/{name}/revoke` - Revoke permission

## Development

### Code Style

- Python: PEP 8
- Structured logging for all components
- Type hints for all functions
- Comprehensive docstrings

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- FastAPI - Web framework
- Pydantic - Data validation
- psutil - System monitoring
- Vosk - Speech-to-text
- OpenCV - Computer vision

## Support

For issues and questions, please open an issue on GitHub.
