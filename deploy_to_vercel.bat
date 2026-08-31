@echo off
REM Personal Expense Intelligence - Quick Deployment to Vercel
REM This script helps prepare the app for Vercel deployment

echo.
echo ================================================================================
echo   PERSONAL EXPENSE INTELLIGENCE - VERCEL DEPLOYMENT HELPER
echo ================================================================================
echo.

REM Verify Git is initialized
if not exist .git (
    echo ERROR: Git repository not initialized
    echo Please run: git init
    exit /b 1
)

echo Step 1: Verifying app integrity...
python -c "from app import app; print('  ✓ App verified')" || (
    echo  ERROR: App verification failed
    exit /b 1
)

echo Step 2: Checking git status...
git status --short

echo.
echo Step 3: DEPLOYMENT REQUIREMENTS (Complete these manually):
echo.
echo   1. CREATE GITHUB REPOSITORY:
echo      - Go to https://github.com/new
echo      - Create a new repository (e.g., 'personalexpenseintelligence')
echo      - Do NOT add README, .gitignore, or license
echo      - Copy the repository URL
echo.
echo   2. CONNECT GITHUB REPOSITORY:
echo      - Run these commands:
echo      - git remote add origin YOUR_REPO_URL
echo      - git push -u origin main
echo.
echo   3. DEPLOY ON VERCEL:
echo      - Go to https://vercel.com/new
echo      - Click "Import Project"
echo      - Paste your GitHub repository URL
echo      - Select "Other" for Framework
echo      - Click "Deploy"
echo.
echo   4. CONFIGURE ENVIRONMENT VARIABLES:
echo      - Go to your Vercel project → Settings → Environment Variables
echo      - Add:
echo        • FLASK_ENV = production
echo        • SECRET_KEY = (generate using: python -c "import secrets; print(secrets.token_hex(32))")
echo.
echo   5. CREATE VERCEL POSTGRES DATABASE:
echo      - Go to Vercel Dashboard → Storage → Create Database → Postgres
echo      - Name it: personal-expense-db
echo      - DATABASE_URL will auto-populate in Environment Variables
echo.
echo   6. REDEPLOY:
echo      - In Vercel Dashboard, click Redeploy on the latest deployment
echo      - Wait for deployment to complete (2-3 minutes)
echo.
echo   7. VERIFY:
echo      - Click "Visit" in Vercel Dashboard
echo      - Login with: demo@expense.ai / password123
echo      - Test all features
echo.
echo ================================================================================
echo For detailed instructions, see: VERCEL_DEPLOYMENT.md
echo ================================================================================
echo.

pause
