# Lyra AI Mark 2 — Client-Server Predecessor

> **Status**: 🗄️ Archived Predecessor  
> **Evolutionary Position**: Original Prototype (Lyra Mark 1) → Lyra Mark 2 (This Repository) → [Lyra Mark 3](https://github.com/Balu-Annapureddy/Lyra-AI-Mark3)  
> **License**: MIT License  

---

## Overview & Historical Lineage

This repository contains **Lyra AI Mark 2**, the intermediate client-server predecessor of the Lyra platform. Mark 2 transitioned Lyra from single-file desktop scripts into a multi-process web architecture featuring a FastAPI backend server, async worker process (`ai-worker`), memory watchdog, dependency injection container, and a Tauri/React desktop UI interface.

```
Lyra Architectural Evolution:
├── Original Lyra (Lyra-My-Personal-AI-Assistant)
│   └── Single-file Python modules (main.py, tts_handler.py, ocr_tools.py, agents.py)
├── Lyra Mark 2 (This Repository - Client-Server Predecessor)
│   └── Multi-process web architecture (FastAPI backend, memory watchdog, Tauri UI)
└── Lyra Mark 3 (Lyra-AI-Mark3 - Active Flagship)
    └── Local-first Personal AI Operating System with intent routing & policy guardrails
```

Development on Mark 2 established the core concepts of memory watchdogs, dry-run safety modes, and model registry constraints that were subsequently refactored into the production local-first AI operating system engine in **Lyra Mark 3**.

---

## Technical Features (Mark 2)

- 🧠 **Local-First Architecture**: Early local model loading pipeline
- 🔐 **Permission System**: Fine-grained RBAC for sensitive system operations
- 📊 **Model Registry**: RAM-aware model cataloging
- 💾 **Memory Watchdog**: System RAM monitoring via `psutil`
- ⚡ **Performance Modes**: Configurable Safe/Balanced execution profiles

---

## Project Status & Archival Notice

This repository is maintained strictly as an **archived historical predecessor** to demonstrate the architectural evolution and progression of the Lyra AI platform. For the active, maintained codebase, visit **[Lyra Mark 3](https://github.com/Balu-Annapureddy/Lyra-AI-Mark3)**.
