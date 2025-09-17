#!/bin/bash

# GeoGuessr League - Secure Setup Script

echo "🔒 Setting up secure GeoGuessr League Dashboard"
echo "=============================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create .env file with your cookies:"
    echo ""
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your actual cookies"
    echo ""
    exit 1
fi

# Check if database exists
if [ ! -f "geoliga.db" ]; then
    echo "❌ Database not found!"
    echo "📝 Please run the league manager first to create the database"
    echo ""
    exit 1
fi

echo "✅ Security setup complete!"
echo ""
echo "🔒 What's secure:"
echo "   - Cookies stored in .env (ignored by Git)"
echo "   - Database ignored by Git"
echo "   - No sensitive data in GitHub"
echo ""
echo "🚀 Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Run: ./setup_github.sh"
echo "2. Create GitHub repository"
echo "3. Deploy to Streamlit Cloud"
echo "4. Upload geoliga.db to Streamlit Cloud manually"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"
