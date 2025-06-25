@echo off
echo 🔑 GitHub Personal Access Token Authentication
echo =============================================
echo.

echo 📋 Instructions:
echo 1. Copy your Personal Access Token from GitHub
echo 2. Run: gh auth login --with-token
echo 3. Paste your token when prompted
echo 4. Press Enter
echo.

echo 🚀 Ready to authenticate? (Press any key to continue)
pause > nul

echo.
echo ⚡ Running authentication...
gh auth login --with-token

echo.
echo ✅ Testing authentication...
gh auth status

echo.
echo 🎯 Testing repository access...
gh repo list --limit 3

echo.
echo 🎉 Authentication test complete!
pause 