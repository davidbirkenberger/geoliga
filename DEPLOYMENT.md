# 🚀 Deployment Guide

## Local Testing

The dashboard is already running locally! You can access it at:
**http://localhost:8501**

## Deploy to Streamlit Community Cloud

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and create a new repository
2. Name it `geoliga` (or any name you prefer)
3. Make it **Public** (required for free Streamlit hosting)
4. Don't initialize with README (we already have files)

### Step 2: Push Your Code

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: GeoGuessr League System"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/geoliga.git

# Push to GitHub
git push -u origin main
```

### Step 3: Deploy to Streamlit

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: `YOUR_USERNAME/geoliga`
5. Set main file path: `dashboard.py`
6. Click "Deploy!"

### Step 4: Share with Friends

Your dashboard will be available at:
**https://YOUR_APP_NAME.streamlit.app**

## Important Notes

### Security Setup
- **Cookies are secure**: Stored in `.env` file (ignored by Git)
- **Database is private**: `geoliga.db` is ignored by Git for security
- **Environment variables**: Use `.env.example` as a template

### Database Location
- The dashboard reads from `geoliga.db` in the same directory
- **Database is NOT uploaded to GitHub** (for security)
- You'll need to manually upload your database file to Streamlit Cloud
- **OR** modify the dashboard to use a cloud database (optional)

### Privacy
- The dashboard URL is public but not discoverable
- Only people with the exact link can access it
- Perfect for sharing with friends!

### Updates
- Any changes you push to GitHub will automatically update the dashboard
- No manual redeployment needed

## Troubleshooting

### Database Not Found
If you see "Database not found" error:
1. Make sure `geoliga.db` is in your GitHub repository
2. Check that the file is not in `.gitignore`

### App Won't Deploy
1. Check that all dependencies are in `requirements.txt`
2. Make sure `dashboard.py` is in the root directory
3. Verify your GitHub repository is public

## Alternative: Keep Database Local

If you prefer to keep your database private, you can:
1. Run the dashboard locally only
2. Share via your local network IP
3. Use a cloud database (PostgreSQL, etc.)

## Next Steps

1. **Test locally** - Make sure everything works
2. **Create GitHub repo** - Push your code
3. **Deploy to Streamlit** - Get your public URL
4. **Share with friends** - Send them the link!

Your friends will love the beautiful dashboard! 🎉
