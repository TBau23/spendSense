# SpendSense Deployment Guide

This guide walks you through deploying SpendSense to Render as a complete demo application.

## Prerequisites

- GitHub account (free)
- Render account (free tier available at [render.com](https://render.com))
- OpenAI API key (from [platform.openai.com](https://platform.openai.com/api-keys))

## Step 1: Push to GitHub

If you haven't already, push your spendSense repository to GitHub:

```bash
# If you haven't initialized git yet
git init
git add .
git commit -m "Initial commit - ready for deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/spendSense.git
git branch -M main
git push -u origin main
```

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up using your GitHub account
3. Authorize Render to access your repositories

## Step 3: Deploy from Blueprint

Render will automatically detect the `render.yaml` file in your repository:

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your `spendSense` repository
3. Render will read `render.yaml` and show two services:
   - **spendsense-api** (Backend Web Service)
   - **spendsense-frontend** (Static Site)
4. Click **"Apply"**

## Step 4: Configure Environment Variables

### Backend Service (`spendsense-api`)

1. Go to the backend service in Render dashboard
2. Navigate to **Environment** tab
3. Add the following environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `FRONTEND_URL` | `https://spendsense-frontend.onrender.com` | Update after frontend deploys |

**Note:** The actual URLs will be assigned by Render. Update `FRONTEND_URL` after both services are deployed.

### Frontend Service (`spendsense-frontend`)

1. Go to the frontend service in Render dashboard
2. Navigate to **Environment** tab
3. Add the following environment variable:

| Key | Value | Notes |
|-----|-------|-------|
| `VITE_API_BASE_URL` | `https://spendsense-api.onrender.com` | Update with actual backend URL |

**Note:** Update this with the actual backend URL after it deploys.

## Step 5: Add Persistent Disk (Backend Only)

The backend needs a persistent disk for the SQLite database:

1. Go to **spendsense-api** service
2. Navigate to **Disks** tab (or **Settings** → **Disks**)
3. Click **"Add Disk"**
4. Configure:
   - **Name:** `spendsense-data`
   - **Mount Path:** `/data`
   - **Size:** 1 GB (minimum)
5. Click **"Create"**

**Important:** The disk name and mount path must match what's in `render.yaml`.

## Step 6: Trigger Deployment

1. Both services should auto-deploy after configuration
2. If not, manually trigger deployment:
   - Go to each service
   - Click **"Manual Deploy"** → **"Deploy latest commit"**

### First Deployment

The first deployment will take 3-5 minutes because:
- Backend installs Python dependencies
- Backend auto-generates demo data (synthetic users, transactions, personas, recommendations)
- Frontend builds the React app

Watch the build logs to see progress.

## Step 7: Update Cross-References

After both services deploy successfully:

1. Note the URLs assigned by Render:
   - Backend: `https://spendsense-api-XXXX.onrender.com`
   - Frontend: `https://spendsense-frontend-YYYY.onrender.com`

2. Update **Backend** environment variable:
   - `FRONTEND_URL` = your frontend URL

3. Update **Frontend** environment variable:
   - `VITE_API_BASE_URL` = your backend URL

4. Trigger a redeploy of both services for changes to take effect

## Step 8: Access Your Demo

Once deployed:

- **Frontend Dashboard:** `https://spendsense-frontend.onrender.com/operator`
- **Backend API Docs:** `https://spendsense-api.onrender.com/docs`
- **Health Check:** `https://spendsense-api.onrender.com/api/health`

## Expected Behavior

### Free Tier Limitations

- **Cold Starts:** Services spin down after 15 minutes of inactivity
- **First Request:** May take 30-60 seconds to wake up
- **Subsequent Requests:** Fast (normal response times)

### Demo Data

The demo includes:
- 75 synthetic users (90% consented)
- 6 months of transaction history
- 5 persona types assigned
- Pre-generated personalized recommendations
- Full operator dashboard functionality

## Troubleshooting

### Build Fails

**"No module named 'backend'"**
- Ensure `PYTHONPATH` is set in `start.sh` (already configured)

**"Database locked"**
- Ensure persistent disk is mounted at `/data` (check disk configuration)

**"OpenAI API error"**
- Verify `OPENAI_API_KEY` is set correctly in backend environment

### Frontend Can't Reach Backend

**CORS errors in browser console**
- Ensure `FRONTEND_URL` is set in backend environment
- Check that the URL matches exactly (with https://)

**API calls return 404**
- Ensure `VITE_API_BASE_URL` is set in frontend environment
- Rebuild frontend after changing environment variables

### Data Not Persisting

**Database resets on every deploy**
- Ensure persistent disk is properly configured and mounted
- Check disk is mounted at `/data` (not `/mnt/data` or other path)

## Redeployment

Subsequent deployments:
- **Backend:** Skips data generation (database exists)
- **Frontend:** Rebuilds React app (fast)
- **Data:** Persists across deployments (stored on disk)

To regenerate data:
1. Delete the persistent disk or database file
2. Redeploy the backend service

## Local Development

The deployment configuration doesn't affect local development:

```bash
# Backend (terminal 1)
cd backend
source venv/bin/activate
python -m uvicorn backend.api.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm run dev
```

Local development uses `data/` directory, production uses `/data` via symlink.

## Cost Estimate

**Free Tier:**
- Backend: 750 hours/month free
- Frontend: Unlimited free (static site)
- Disk: First 1GB free
- **Total: $0/month** (sufficient for demo)

**Paid Tier (Optional):**
- If you need 24/7 uptime without cold starts: ~$7/month per service

## Support

For Render-specific issues:
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)

For SpendSense issues:
- Check the main README.md
- Review logs in Render dashboard

