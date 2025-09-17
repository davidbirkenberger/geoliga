#!/usr/bin/env python3
"""
Start a new GeoGuessr League Challenge

This script helps you start a new weekly challenge.
"""

import sys
from league_manager import LeagueManager

def main():
    print("🌍 GeoGuessr League - Challenge Starter")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python start_challenge.py <challenge_id> [map_name]")
        print("\nExample:")
        print("  python start_challenge.py FbxiQzxzq9XuwwY2 'A Community World'")
        print("\nTo get a challenge ID:")
        print("  1. Go to geoguessr.com")
        print("  2. Create a new challenge")
        print("  3. Copy the challenge ID from the URL")
        sys.exit(1)
    
    challenge_id = sys.argv[1]
    map_name = sys.argv[2] if len(sys.argv) > 2 else "Weekly Challenge"
    
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
    result = league.create_challenge(challenge_id, map_name)
    
    if result:
        print("✅ Challenge created successfully!")
        print(f"📅 Week: {league.get_current_week()}")
        print()
        print("🎮 Next steps:")
        print("1. Share the challenge link with your friends")
        print("2. Play the challenge yourself")
        print("3. Check results anytime with: python weekly_league.py process " + challenge_id)
        print("4. Close the challenge on Sunday with: python weekly_league.py close " + challenge_id)
        print()
        print("📱 View standings: python weekly_league.py standings")
    else:
        print("❌ Failed to create challenge")
        sys.exit(1)

if __name__ == "__main__":
    main()
