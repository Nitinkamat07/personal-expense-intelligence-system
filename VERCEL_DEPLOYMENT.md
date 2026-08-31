# Vercel Deployment Guide

This guide provides step-by-step instructions to deploy the Personal Expense Intelligence System to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **GitHub/GitLab/Bitbucket Account**: For git repository hosting
3. **Vercel CLI** (optional): For manual deployment from terminal

## Step 1: Prepare Your Git Repository

```powershell
# Initialize git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: Personal Expense Intelligence System"
```

## Step 2: Push to GitHub (or your preferred git provider)

1. Create a new repository on GitHub (without README, .gitignore, license)
2. Add the remote and push:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/your-repo-name.git
git branch -M main
git push -u origin main
```

## Step 3: Create Vercel Project

### Option A: Using Vercel Dashboard (Recommended for first-time)

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Select the repository you just created
5. Framework: **Other** (since it's using Python Flask)
6. Root Directory: `.` (current directory)
7. Build Command: Leave empty (not needed for Python)
8. Output Directory: Leave empty
9. Click "Deploy"

### Option B: Using Vercel CLI

```powershell
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from your project directory
vercel --prod
```

## Step 4: Configure Environment Variables

After deployment, you need to set up the database and environment variables:

### In Vercel Dashboard:

1. Go to your project → Settings → Environment Variables
2. Add the following variables:

```
FLASK_ENV = production
SECRET_KEY = (generate a strong random string, e.g., using python: python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL = (will be provided by Vercel Postgres)
```

### Create Vercel Postgres Database:

1. In Vercel Dashboard → Storage → Create new database → Postgres
2. The `DATABASE_URL` will be automatically added to your environment variables
3. Redeploy your project (push to main branch or click "Redeploy")

## Step 5: First-Time Database Setup

The app will automatically:
- ✅ Create database schema
- ✅ Create a demo user (demo@expense.ai / password123)
- ✅ Train the ML categorizer on sample data

Just log in after the first deployment!

## Step 6: Monitor Deployment

```powershell
# View deployment logs in Vercel Dashboard
# Go to your project → Deployments → click the latest deployment → Logs
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
- Ensure all dependencies are in `requirements.txt`
- Rebuild: `vercel --prod --force`

### "Database connection refused"
- Check DATABASE_URL is set in Environment Variables
- Verify Postgres database is created and running
- Redeploy: `vercel --prod`

### "500 Internal Server Error"
- Check Vercel logs: Dashboard → Deployments → Logs
- Verify all environment variables are set
- Check config.py database URL handling

### App won't start
- Verify wsgi.py exists and is correct
- Check vercel.json routes configuration
- Ensure SECRET_KEY is set in environment

## Post-Deployment

### Generate a Strong SECRET_KEY

```powershell
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Add this value to Vercel Environment Variables.

### Update Demo User Password (Recommended)

1. Log in with demo@expense.ai / password123
2. Change password in settings
3. Update in production database if needed

### Monitor Logs

```powershell
# If using Vercel CLI
vercel logs
```

## Performance Notes

- First request may take 5-10 seconds (cold start on serverless)
- Database queries are optimized with connection pooling
- Static files (CSS, JS) are served efficiently
- ML categorization runs in-process

## Database Limits

- Vercel Postgres free tier: Suitable for personal use
- Upgrade plan if exceeding limits

## Helpful Links

- Vercel Python Docs: https://vercel.com/docs/functions/python
- Vercel Postgres: https://vercel.com/storage/postgres
- Vercel Environment Variables: https://vercel.com/docs/projects/environment-variables

---

**Note**: Do not commit `.env` file to git. Environment variables should be set only in Vercel dashboard.
