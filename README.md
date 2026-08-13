# Lyra Mark 2 — Archived Predecessor

> 🗄️ Historical predecessor of [Lyra](https://github.com/Balu-Annapureddy/Lyra).

This repository contains the second architectural generation of Lyra. It is preserved for historical and engineering reference. Active development has moved to the current [Lyra](https://github.com/Balu-Annapureddy/Lyra) repository.

---

## Overview & Historical Lineage

**Lyra AI Mark 2** transitioned Lyra from single-file desktop scripts into a multi-process web architecture featuring a FastAPI backend server, async worker process (`ai-worker`), memory watchdog, dependency injection container, and a Tauri/React desktop UI interface.

```
Lyra Architectural Evolution:
├── Original Lyra (Lyra-My-Personal-AI-Assistant - Mark 1)
│   └── Single-file Python modules (main.py, tts_handler.py, ocr_tools.py, agents.py)
├── Lyra Mark 2 (This Repository - Client-Server Predecessor)
│   └── Multi-process web architecture (FastAPI backend, memory watchdog, Tauri UI)
└── Lyra (Lyra - Active Flagship)
    └── Local-first Personal AI Operating System with intent routing & policy guardrails
```

Development on Mark 2 established the core concepts of memory watchdogs, dry-run safety modes, and model registry constraints that were subsequently refactored into the active local-first AI operating system engine in **[Lyra](https://github.com/Balu-Annapureddy/Lyra)**.

---

## Technical Features (Mark 2)

- 🧠 **Local-First Architecture**: Early local model loading pipeline
- 🔐 **Permission System**: Fine-grained RBAC for sensitive system operations
- 📊 **Model Registry**: RAM-aware model cataloging
- 💾 **Memory Watchdog**: System RAM monitoring via `psutil`
- ⚡ **Performance Modes**: Configurable Safe/Balanced execution profiles

---

## Status & Development Note

This project was superseded by the next Lyra generation before phase 4 integration was completed. This repository is preserved strictly as an **archived historical predecessor** to demonstrate the architectural evolution and progression of the Lyra AI platform.

For the active, maintained codebase, visit **[Lyra](https://github.com/Balu-Annapureddy/Lyra)**.
