#!/usr/bin/env python3
"""
Start a new GeoGuessr League Challenge

This script helps you start a new weekly challenge.
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from league_manager import LeagueManager

TZ = ZoneInfo("Europe/Berlin")

def main():
    print("🌍 GeoGuessr League - Challenge Starter")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python start_challenge.py <challenge_id> [map_name] [end_date]")
        print("\nExample:")
        print("  python start_challenge.py FbxiQzxzq9XuwwY2 'A Community World'")
        print("  python start_challenge.py FbxiQzxzq9XuwwY2 'A Community World' 2024-01-15")
        print("\nTo get a challenge ID:")
        print("  1. Go to geoguessr.com")
        print("  2. Create a new challenge")
        print("  3. Copy the challenge ID from the URL")
        print("\nend_date format: YYYY-MM-DD (e.g., 2024-01-15)")
        print("If no end_date provided, challenge runs until end of current week")
        sys.exit(1)
    
    challenge_id = sys.argv[1]
    map_name = sys.argv[2] if len(sys.argv) > 2 else "Weekly Challenge"
    end_date = None
    
    # Parse end_date if provided
    if len(sys.argv) > 3:
        try:
            end_date = datetime.strptime(sys.argv[3], '%Y-%m-%d').replace(tzinfo=TZ)
        except ValueError:
            print("❌ Invalid end_date format. Use YYYY-MM-DD (e.g., 2024-01-15)")
            sys.exit(1)
    
    print(f"🎯 Starting challenge: {challenge_id}")
    print(f"🗺️  Map: {map_name}")
    print()
    
    # Initialize league manager
    try:
        league = LeagueManager()
        print("✅ League manager initialized")
    except Exception as e:
        print(f"❌ Error initializing league manager: {e}")
        print("Make sure your .env file is set up correctly!")
        sys.exit(1)
    
    # Create challenge
    print("📝 Creating challenge...")
    result = league.create_challenge(challenge_id, map_name, end_date=end_date)
    
    if result:
        print("✅ Challenge created successfully!")
        print(f"📅 Week: {league.get_current_week()}")
        if end_date:
            print(f"⏰ Challenge ends: {end_date.strftime('%Y-%m-%d %H:%M')} CET")
        else:
            print("⏰ Challenge ends: End of current week")
        print()
        print("🎮 Next steps:")
        print("1. Share the challenge link with your friends")
        print("2. Play the challenge yourself")
        print("3. Check results anytime with: python weekly_league.py process " + challenge_id)
        print("4. Results count directly into overall standings!")
        print()
        print("📱 View standings: python weekly_league.py standings")
        print("📊 View league: python weekly_league.py league")
    else:
        print("❌ Failed to create challenge")
        sys.exit(1)

if __name__ == "__main__":
    main()
