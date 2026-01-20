# Railway Deployment Guide

This guide explains how to deploy Harpoon to Railway, assuming you already have a Railway project with PostgreSQL set up.

## Prerequisites

- Railway account with an existing project
- PostgreSQL database already provisioned in Railway
- GitHub repository connected to Railway

## Project Structure

Harpoon consists of two services:
- **Backend**: FastAPI application (Python)
- **Frontend**: Next.js application (Node.js)

## Step 1: Add Backend Service

1. In your Railway project, click **"New Service"** → **"GitHub Repo"**
2. Select the `harpoon` repository
3. Configure the service:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `sh -c 'uvicorn app.main:app --host 0.0.0.0 --port $PORT'`

> **Important**: The `sh -c '...'` wrapper is required for Railway to expand the `$PORT` environment variable.

### Backend Environment Variables

Add these environment variables to the backend service:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
GAMMA_API_URL=https://gamma-api.polymarket.com
ORDERS_SUBGRAPH_URL=https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/polymarket-orderbook-resync/prod/gn
ACTIVITY_SUBGRAPH_URL=https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/polymarket-activity-tracker-base/prod/gn
```

Note: `${{Postgres.DATABASE_URL}}` is a Railway reference variable that automatically connects to your PostgreSQL service.

### Database Migration

The tables are created automatically on first run via SQLAlchemy's `create_all()`. No manual migration needed.

## Step 2: Add Frontend Service

1. Click **"New Service"** → **"GitHub Repo"**
2. Select the same `harpoon` repository
3. Configure the service:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Start Command**: `npm start`

> **Note**: Use `npm ci` instead of `npm install` for faster, more reliable builds in CI/CD environments.

### Frontend Environment Variables

```
NEXT_PUBLIC_API_URL=https://<your-backend-service>.railway.app
```

Replace `<your-backend-service>` with your backend's Railway domain (found in the backend service's Settings → Networking → Public Domain).

## Step 3: Configure Networking

### Backend
1. Go to backend service → **Settings** → **Networking**
2. Click **"Generate Domain"** to get a public URL
3. Copy this URL for the frontend's `NEXT_PUBLIC_API_URL`

### Frontend
1. Go to frontend service → **Settings** → **Networking**
2. Click **"Generate Domain"** for the public-facing URL
3. Optionally add a custom domain

## Step 4: Configure Health Checks (Optional)

For the backend service:
- **Health Check Path**: `/health` (if you add a health endpoint) or leave empty
- **Restart Policy**: On Failure

## Environment Variables Reference

### Backend (Required)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `${{Postgres.DATABASE_URL}}` |
| `GAMMA_API_URL` | Polymarket Gamma API | `https://gamma-api.polymarket.com` |
| `ORDERS_SUBGRAPH_URL` | TheGraph subgraph for orders | See above |
| `ACTIVITY_SUBGRAPH_URL` | TheGraph subgraph for activity | See above |

### Frontend (Required)
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://harpoon-backend.railway.app` |

## Connecting to Existing PostgreSQL

If your PostgreSQL is already set up in Railway:

1. Go to your PostgreSQL service in Railway
2. Copy the connection string from **Variables** → `DATABASE_URL`
3. Add it to your backend service's environment variables

Or use Railway's reference syntax:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

This automatically references the PostgreSQL service named "Postgres" in your project.

## Troubleshooting

### Backend not connecting to database
- Ensure `DATABASE_URL` is correctly set
- Check that the PostgreSQL service is running
- Verify the database name in the connection string

### Frontend not loading data
- Verify `NEXT_PUBLIC_API_URL` points to the correct backend URL
- Check backend logs for any API errors
- Ensure CORS is properly configured (should work by default)

### Build failures
- Check the build logs in Railway
- Ensure all dependencies are in `requirements.txt` (backend) or `package.json` (frontend)

## Local Development with Railway Database

To connect locally to your Railway PostgreSQL:

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Link project: `railway link`
4. Run with Railway env: `railway run uvicorn app.main:app --reload`

Or copy the `DATABASE_URL` from Railway and add it to a local `.env` file.

## Deployment Commands

Railway deploys automatically when you push to the connected branch. To manually trigger:

```bash
# Using Railway CLI
railway up
```

Or push to your GitHub repository:
```bash
git push origin main
```
