# Lyra AI Mark2 - Railway Deployment Guide

## Quick Deploy to Railway

### 1. Prerequisites
- Railway account: https://railway.app
- GitHub repository connected to Railway

### 2. Deploy Steps

#### Option A: Deploy from GitHub (Recommended)
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your `Lyra-Ai-Mark2-` repository
4. Railway will auto-detect the configuration

#### Option B: Deploy with Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 3. Configure Environment Variables

In Railway dashboard, add these variables:

**Required:**
```
PORT=8000  # Railway sets this automatically
LYRA_ENV=production
LOG_LEVEL=INFO
```

**Optional (Recommended):**
```
MAX_WORKERS=2
CACHE_MAX_SIZE_GB=5
MEMORY_LIMIT_PERCENT=85
ALLOWED_ORIGINS=https://your-frontend.com
```

### 4. Configuration Files

Railway uses these files:
- **`railway.json`**: Build and deploy configuration
- **`Procfile`**: Start command
- **`ai-worker/gunicorn_railway.py`**: Gunicorn config
- **`ai-worker/requirements.txt`**: Python dependencies

### 5. Verify Deployment

After deployment:
1. Railway will provide a URL: `https://your-app.railway.app`
2. Test endpoints:
   ```bash
   curl https://your-app.railway.app/health
   curl https://your-app.railway.app/status
   ```

### 6. Monitor Application

Railway Dashboard shows:
- Deployment logs
- Resource usage
- Application metrics
- Environment variables

### 7. Custom Domain (Optional)

1. Go to Railway project settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as shown

### 8. Scaling

Railway automatically scales based on:
- Traffic
- Resource usage
- Plan limits

For manual scaling:
1. Adjust `WEB_CONCURRENCY` environment variable
2. Upgrade Railway plan for more resources

### 9. Troubleshooting

**Build fails:**
- Check `railway.json` build command
- Verify `requirements.txt` is correct
- Check Railway build logs

**App crashes:**
- Check Railway logs
- Verify environment variables
- Check memory limits

**Slow response:**
- Increase `MAX_WORKERS`
- Upgrade Railway plan
- Check `/status` endpoint for warnings

### 10. Cost Optimization

Railway pricing tips:
- Start with Hobby plan ($5/month)
- Monitor resource usage in dashboard
- Optimize `CACHE_MAX_SIZE_GB` for your plan
- Use Railway's free tier for testing

### 11. Important Notes

- **No venv needed**: Railway manages Python environment
- **Port binding**: Uses `PORT` environment variable
- **Logs**: Available in Railway dashboard
- **Restarts**: Automatic on failure (max 3 retries)
- **Build time**: ~2-3 minutes

### 12. Production Checklist

Before going live:
- [ ] Set `LYRA_ENV=production`
- [ ] Configure `ALLOWED_ORIGINS`
- [ ] Set strong `SECRET_KEY`
- [ ] Test all endpoints
- [ ] Monitor resource usage
- [ ] Set up custom domain
- [ ] Configure error alerting

---

## Railway vs Self-Hosted

| Feature | Railway | Self-Hosted |
|---------|---------|-------------|
| Setup Time | 5 minutes | 1-2 hours |
| Scaling | Automatic | Manual |
| SSL/HTTPS | Included | Configure yourself |
| Monitoring | Built-in | Setup required |
| Cost | $5-20/month | Server costs |
| Maintenance | Managed | DIY |

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/Balu-Annapureddy/Lyra-Ai-Mark2-/issues
