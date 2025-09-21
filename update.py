#!/usr/bin/env python3
"""
Update Script for GeoGuessr League

Usage:
  python update.py <challenge_id>           # Update specific challenge
  python update.py --active                # Update all active challenges
  python update.py --all                   # Update all challenges
"""

import sys
import subprocess
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

def get_active_challenges():
    """Get all active challenges from database."""
    conn = sqlite3.connect("geoliga.db")
    cursor = conn.cursor()
    
    current_time = datetime.now(TZ)
    cursor.execute('''
        SELECT challenge_id FROM challenges 
        WHERE status = 'active' AND end_date > ?
    ''', (current_time.date(),))
    
    challenges = [row[0] for row in cursor.fetchall()]
    conn.close()
    return challenges

def get_all_challenges():
    """Get all challenges from database."""
    conn = sqlite3.connect("geoliga.db")
    cursor = conn.cursor()
    
    cursor.execute('SELECT challenge_id FROM challenges')
    challenges = [row[0] for row in cursor.fetchall()]
    conn.close()
    return challenges

def update_challenge(challenge_id):
    """Update a single challenge."""
    print(f"🔄 Processing challenge {challenge_id}...")
    result = subprocess.run(f"python weekly_league.py process {challenge_id}", shell=True)
    if result.returncode == 0:
        print(f"✅ Challenge {challenge_id} updated successfully")
        return True
    else:
        print(f"❌ Failed to update challenge {challenge_id}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python update.py <challenge_id>    # Update specific challenge")
        print("  python update.py --active          # Update all active challenges")
        print("  python update.py --all             # Update all challenges")
        sys.exit(1)

    arg = sys.argv[1]
    
    if arg == "--active":
        print("🚀 Updating all active challenges...")
        challenges = get_active_challenges()
        if not challenges:
            print("ℹ️ No active challenges found")
            return
        print(f"📋 Found {len(challenges)} active challenges: {', '.join(challenges)}")
        
    elif arg == "--all":
        print("🚀 Updating all challenges...")
        challenges = get_all_challenges()
        if not challenges:
            print("ℹ️ No challenges found in database")
            return
        print(f"📋 Found {len(challenges)} challenges: {', '.join(challenges)}")
        
    else:
        # Single challenge ID
        challenges = [arg]
        print(f"🚀 Updating challenge {arg}...")

    # Process all challenges
    success_count = 0
    for challenge_id in challenges:
        if update_challenge(challenge_id):
            success_count += 1

    print(f"\n📊 Updated {success_count}/{len(challenges)} challenges")

    if success_count > 0:
        # Add, commit, push
        print("📤 Committing and pushing changes...")
        subprocess.run("git add .", shell=True)
        
        if len(challenges) == 1:
            commit_msg = f"Update results for {challenges[0]}"
        else:
            commit_msg = f"Update results for {len(challenges)} challenges"
            
        subprocess.run(f'git commit -m "{commit_msg}"', shell=True)
        subprocess.run("git push", shell=True)
        print("✅ Done! Dashboard updated.")
    else:
        print("❌ No challenges were updated successfully")

if __name__ == "__main__":
    main()
