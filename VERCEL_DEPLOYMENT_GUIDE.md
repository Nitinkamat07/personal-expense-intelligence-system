# 🚀 Vercel Deployment Guide - Personal Expense Intelligence

## Prerequisites
- GitHub account (already connected ✅)
- Vercel account (free: https://vercel.com/signup)
- PostgreSQL database (Vercel Postgres - free tier available)

---

## Step 1: Create Vercel Postgres Database

### Option A: Use Vercel Postgres (Recommended - Free)
1. Go to https://vercel.com/dashboard
2. Click "Storage" → "Create Database"
3. Select "Postgres"
4. Name: `personal-expense-intelligence-db`
5. Select region close to you
6. Click "Create"
7. Copy the connection string (starts with `postgresql://`)

### Option B: Use External PostgreSQL (Neon, Railway, etc.)
- Use any PostgreSQL provider
- Get the `postgresql://username:password@host:port/database` connection string

---

## Step 2: Deploy to Vercel

### Method 1: Web Dashboard (Easiest)

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click "Add New..." → "Project"**
3. **Select "Import Git Repository"**
4. **Search for**: `Nitinkamat07/personal-expense-intelligence-system`
5. **Click "Import"**
6. **Configure Project Settings**:
   - Framework Preset: Python
   - Root Directory: `.` (default)
   - Build Command: Leave empty (Vercel auto-detects)
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements.txt`

7. **Add Environment Variables** (Click "Environment Variables"):
   ```
   FLASK_ENV = production
   SECRET_KEY = (generate a random 32-character string)
   DATABASE_URL = (paste your PostgreSQL connection string from Step 1)
   ```

8. **Click "Deploy"**
9. **Wait 2-3 minutes** for deployment to complete

### Method 2: Vercel CLI (Advanced)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to project directory
cd c:\Users\nitin\Desktop\anti

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

---

## Step 3: Set Up Database

After deployment completes:

1. Go to your Vercel project dashboard
2. Click "Deployments" → Latest deployment
3. Copy the URL (e.g., `https://personal-expense-intelligence-system.vercel.app`)

4. **Initialize Database** by visiting:
   ```
   https://your-vercel-url.vercel.app/
   ```
   This will:
   - Create all necessary tables
   - Seed demo user (demo@expense.ai / password123)
   - Train ML categorizer

---

## Step 4: Verify Deployment

### Test Login:
- **Email**: demo@expense.ai
- **Password**: password123
- **Expected**: Dashboard loads with transactions

### Check Application Health:
1. Visit: `https://your-vercel-url.vercel.app/`
2. Should redirect to login page (200 OK)
3. Login with demo credentials
4. Test Features:
   - Add Expense
   - View Dashboard
   - Export CSV
   - Check Insights

---

## Troubleshooting

### Issue: "Database connection error"
**Solution:**
1. Verify `DATABASE_URL` is set in Vercel Environment Variables
2. Check PostgreSQL connection string format: `postgresql://user:pass@host/db`
3. Ensure firewall allows Vercel IPs (usually auto-allowed)

### Issue: "Module not found" or "Import error"
**Solution:**
1. Check `requirements.txt` is in root directory
2. Verify all dependencies are listed
3. Redeploy: `vercel --prod`

### Issue: "ML Model training fails"
**Solution:**
1. This is expected on first deployment (model trains automatically)
2. Wait 1-2 minutes, refresh the page
3. Check `/ml/models/` directory exists

### Issue: "Static files (CSS/JS) not loading"
**Solution:**
1. Ensure `static/` folder is in git repository
2. Check `wsgi.py` correctly serves static files
3. Clear browser cache (Ctrl+Shift+Delete) and refresh

---

## Environment Variables Checklist

Make sure these are set in Vercel:

| Variable | Value | Required |
|----------|-------|----------|
| `FLASK_ENV` | `production` | ✅ Yes |
| `SECRET_KEY` | Random 32+ char string | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |

---

## Security Checklist

✅ `SECRET_KEY` is set (not hardcoded)
✅ `DATABASE_URL` is in environment variables (not git)
✅ CSRF protection enabled
✅ SQL injection protected (SQLAlchemy ORM)
✅ Password hashing with Werkzeug

---

## Post-Deployment Setup (Optional)

### 1. Custom Domain
- In Vercel: Settings → Domains
- Add your custom domain

### 2. SSL Certificate
- Automatic (Vercel provides free SSL)

### 3. Monitoring
- Vercel Analytics: https://vercel.com/analytics
- Check deployments, errors, performance

### 4. Automatic Deployments
- Already enabled: Push to `main` branch = auto-deploy
- No need for manual CI/CD setup

---

## Production Database Migration

If you want to switch from SQLite (development) to PostgreSQL (production):

1. Existing data in SQLite will NOT automatically migrate
2. Demo user will be created on first deployment
3. For production data: Export from dev, import to production

### Backup Production Data:
```bash
# On Vercel PostgreSQL
pg_dump "your-database-url" > backup.sql
```

---

## Rollback / Revert Deployment

1. Go to Vercel Dashboard → Deployments
2. Find previous working version
3. Click "..." → "Promote to Production"

---

## Next Steps

1. ✅ Create Vercel account
2. ✅ Create PostgreSQL database
3. ✅ Deploy via web dashboard or CLI
4. ✅ Set environment variables
5. ✅ Test login and features
6. ✅ Share URL: `https://your-vercel-url.vercel.app`

---

## Support

- Vercel Docs: https://vercel.com/docs
- Flask Deployment: https://flask.palletsprojects.com/deployment/
- GitHub Issues: https://github.com/Nitinkamat07/personal-expense-intelligence-system/issues

---

**All files are ready for Vercel. Just follow the steps above! 🚀**
