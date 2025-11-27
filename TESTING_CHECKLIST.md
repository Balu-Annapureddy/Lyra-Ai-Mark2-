# Lyra AI Mark2 - Manual Testing Checklist

## Pre-Flight Checks

Run the verification script first:
```bash
verify_setup.bat
```

This checks:
- ✅ Python installed
- ✅ Node.js installed
- ✅ Virtual environment exists
- ✅ Backend files present
- ✅ Frontend files present
- ✅ Dependencies installed

---

## Step 1: Start Backend

### Terminal 1
```bash
cd C:\Users\annap\Desktop\Projects\Lyra-Mark2
start.bat
```

### Expected Output
```
============================================================
Lyra AI Mark2 - Starting...
============================================================
GPU: [GPU Name] (nvidia/amd/none)
GPU self-test: X passed, Y failed
Performance mode: eco/balanced/performance
Memory watchdog started
Job scheduler ready
Lazy loader auto-unload started
Registered 5 skills
============================================================
Lyra AI Mark2 - Ready!
Session ID: 20251125_XXXXXX
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Verify Backend
Open browser: http://localhost:8000

**Expected**: JSON response
```json
{
  "name": "Lyra AI Mark2",
  "version": "2.0.0",
  "status": "running",
  "session_id": "...",
  "session_duration": ...
}
```

---

## Step 2: Test Backend Endpoints

### Health Check
```bash
curl http://localhost:8000/health/
```

**Expected**: `{"status": "healthy", ...}`

### GPU Status
```bash
curl http://localhost:8000/health/gpu
```

**Expected**: GPU info or degraded status

### Models List
```bash
curl http://localhost:8000/models
```

**Expected**: `{"models": [...]}`

---

## Step 3: Start Frontend

### Terminal 2
```bash
cd C:\Users\annap\Desktop\Projects\Lyra-Mark2
start-frontend.bat
```

### Expected Output
```
Installing dependencies... (first time only)
Starting development server...
Frontend will be available at: http://localhost:5173

VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## Step 4: Test Frontend

### Open Browser
Navigate to: http://localhost:5173

### Expected UI
- ✅ Dark theme background with gradient
- ✅ Header: "Lyra AI Mark2" with logo
- ✅ Main content: "Model Manager" title
- ✅ Model cards (if models configured)
- ✅ Footer: Version info

### Check Console (F12)
- ✅ No errors in console
- ✅ API calls to `/api/models` succeed

---

## Step 5: Test Model Manager Features

### If Models Are Configured
- ✅ Model cards display correctly
- ✅ Download button appears for uninstalled models
- ✅ Clicking download starts job
- ✅ Progress indicator shows
- ✅ Install status updates after download
- ✅ Delete button appears for installed models

### If No Models
- ✅ Shows "No models available" message
- ✅ No errors in console

---

## Common Issues & Fixes

### Backend Issues

**Issue**: `ModuleNotFoundError`
```bash
# Fix: Install dependencies
setup_venv.bat
```

**Issue**: `Port 8000 already in use`
```bash
# Fix: Kill existing process
taskkill /F /IM python.exe
# Or change port in app.py
```

**Issue**: Import errors
```bash
# Fix: Reinstall dependencies
venv\Scripts\activate
pip install -r ai-worker\requirements-lightweight.txt
```

### Frontend Issues

**Issue**: `Cannot find module`
```bash
# Fix: Install dependencies
cd frontend
npm install
```

**Issue**: `ERR_CONNECTION_REFUSED`
```bash
# Fix: Start backend first
# Backend must be running on port 8000
```

**Issue**: Blank page
```bash
# Fix: Check browser console (F12)
# Look for API errors
# Verify backend is responding
```

---

## Success Criteria

✅ Backend starts without errors  
✅ Backend responds to health checks  
✅ Frontend loads without errors  
✅ Frontend displays Model Manager UI  
✅ API calls succeed (check Network tab)  
✅ No console errors  

---

## Next Steps After Verification

1. ✅ Both servers running
2. 📝 Configure model registry (add models)
3. 🧪 Run E2E smoke tests
4. 🎨 Test download functionality
5. 🚀 Proceed with alpha testing

---

## Need Help?

If you encounter issues:
1. Run `verify_setup.bat` first
2. Check the logs in both terminals
3. Look for error messages
4. Verify all dependencies are installed
