# 🚀 Quick Start Guide - Lyra AI Mark2

## ⚠️ Important: Start Backend First!

The frontend needs the backend API to be running. Always start the backend before the frontend.

---

## Step-by-Step Startup

### 1. Start Backend (Terminal 1)

```bash
cd C:\Users\annap\Desktop\Projects\Lyra-Mark2
start.bat
```

**Wait for this message**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Frontend (Terminal 2)

```bash
cd C:\Users\annap\Desktop\Projects\Lyra-Mark2
start-frontend.bat
```

**Wait for this message**:
```
Local: http://localhost:5173/
```

### 3. Open Browser

Navigate to: **http://localhost:5173**

---

## First-Time Setup (If Not Done)

### Backend Setup
```bash
cd C:\Users\annap\Desktop\Projects\Lyra-Mark2
setup_venv.bat
```

### Frontend Setup
```bash
cd frontend
npm install
```

---

## Troubleshooting

### "ERR_CONNECTION_REFUSED"
- ✅ **Solution**: Start the backend first (`start.bat`)
- Backend must be running on port 8000 before frontend can connect

### "ModuleNotFoundError"
- ✅ **Solution**: Run `setup_venv.bat` to install Python dependencies

### "Cannot find module" (Frontend)
- ✅ **Solution**: Run `npm install` in `frontend/` directory

### Port Already in Use
- ✅ **Solution**: Kill existing process or restart computer

---

## Quick Test

After both servers are running:

1. **Backend**: http://localhost:8000/health/
2. **Frontend**: http://localhost:5173

Both should load successfully!
