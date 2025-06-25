@echo off
echo 🚀 Solutio 360 Community Edition - GitHub Upload
echo ============================================
echo.

echo 📝 Step 1: Adding GitHub remote...
git remote add origin https://github.com/YOUR_USERNAME/solutio-360-community.git

echo.
echo 📤 Step 2: Pushing to GitHub...
git push -u origin main

echo.
echo ✅ Step 3: Verification...
git remote -v

echo.
echo 🎉 SUCCESS! Repository uploaded to GitHub
echo 📋 Next steps:
echo    1. Visit your repository on GitHub
echo    2. Add repository topics: django, pwa, complaint-management, python, open-source
echo    3. Enable GitHub Pages (optional)
echo    4. Configure repository settings
echo.
pause 