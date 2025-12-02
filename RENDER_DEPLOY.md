# Render Deployment Guide for Lyra AI Mark2

## Quick Deploy to Render

### Option 1: One-Click Deploy (Recommended)

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Balu-Annapureddy/Lyra-Ai-Mark2-`
   - Render will automatically detect `render.yaml`
   - Click "Apply" to deploy

3. **Done!** Your app will be live at: `https://lyra-ai-mark2.onrender.com`

---

### Option 2: Manual Configuration

If you prefer manual setup:

1. **Create New Web Service** on Render
2. **Configure Build Settings**:
   - **Build Command**: `cd ai-worker && pip install -r requirements.txt`
   - **Start Command**: `cd ai-worker && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: `3.12.0`

3. **Set Environment Variables** (optional):
   ```
   ALLOWED_ORIGINS=https://your-frontend.com
   LOG_LEVEL=INFO
   PERFORMANCE_MODE=balanced
   ```

4. **Deploy**: Click "Create Web Service"

---

## Environment Variables

Configure these in Render Dashboard → Environment:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Server port | `10000` | Auto-set by Render |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000,http://localhost:5173` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `PERFORMANCE_MODE` | Performance mode | `balanced` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | No |
| `GOOGLE_API_KEY` | Google API key | - | No |

---

## Health Check

Render will automatically monitor: `https://your-app.onrender.com/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-02T12:00:00",
  "version": "2.0.0"
}
```

---

## API Documentation

Once deployed, access interactive API docs:
- **Swagger UI**: `https://your-app.onrender.com/docs`
- **ReDoc**: `https://your-app.onrender.com/redoc`

---

## Troubleshooting

### Build Fails
- Check that `requirements.txt` is in `ai-worker/` directory
- Verify Python version is 3.12.0
- Check build logs in Render dashboard

### App Crashes on Startup
- Check logs in Render dashboard
- Verify all dependencies are installed
- Ensure `PORT` environment variable is set

### CORS Errors
- Add your frontend URL to `ALLOWED_ORIGINS` environment variable
- Format: `https://frontend1.com,https://frontend2.com`

### Health Check Fails
- Verify `/health` endpoint returns 200 status
- Check application logs for errors

---

## Free Tier Limitations

Render Free Tier includes:
- ✅ 750 hours/month (enough for 24/7 uptime)
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold start takes ~30 seconds

**Tip**: Upgrade to Starter ($7/month) for always-on service.

---

## Post-Deployment

1. **Test the API**:
   ```bash
   curl https://your-app.onrender.com/health
   ```

2. **View Logs**: Render Dashboard → Logs tab

3. **Monitor**: Render Dashboard → Metrics tab

4. **Update**: Push to GitHub → Auto-deploys

---

## Production Checklist

- [x] `render.yaml` configured
- [x] `uvicorn[standard]` in requirements.txt
- [x] Production CORS settings
- [x] Health check endpoint
- [x] Environment variables configured
- [x] API documentation enabled
- [ ] Custom domain (optional)
- [ ] Monitoring/alerts (optional)

---

## Next Steps

1. Deploy to Render
2. Test all endpoints
3. Configure custom domain (optional)
4. Set up monitoring (optional)
5. Add frontend deployment (optional)
