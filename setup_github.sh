#!/bin/bash

# GeoGuessr League - GitHub Setup Script

echo "🚀 Setting up GitHub repository for GeoGuessr League Dashboard"
echo "=============================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit
echo "💾 Committing changes..."
git commit -m "Initial commit: GeoGuessr League System with Streamlit Dashboard"

echo ""
echo "✅ Ready for GitHub!"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com and create a new repository"
echo "2. Name it 'geoliga' (or any name you prefer)"
echo "3. Make it PUBLIC (required for free Streamlit hosting)"
echo "4. Don't initialize with README"
echo "5. Copy the repository URL"
echo "6. Run these commands:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/geoliga.git"
echo "   git push -u origin main"
echo ""
echo "7. Then go to https://share.streamlit.io to deploy!"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"
