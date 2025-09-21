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
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from db_lock import db_lock

TZ = ZoneInfo("Europe/Berlin")

def get_db_connection():
    """Get a database connection with proper cleanup."""
    conn = sqlite3.connect("geoliga.db", timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
    conn.execute("PRAGMA journal_mode = WAL")    # Better concurrency
    return conn

def get_active_challenges():
    """Get all active challenges from database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now(TZ)
        cursor.execute('''
            SELECT challenge_id FROM challenges 
            WHERE status = 'active' AND end_date > ?
        ''', (current_time.date(),))
        
        challenges = [row[0] for row in cursor.fetchall()]
        return challenges
    finally:
        conn.close()

def get_all_challenges():
    """Get all challenges from database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT challenge_id FROM challenges')
        challenges = [row[0] for row in cursor.fetchall()]
        return challenges
    finally:
        conn.close()

def update_challenge(challenge_id, max_retries=3):
    """Update a single challenge with retry logic."""
    print(f"🔄 Processing challenge {challenge_id}...")
    
    for attempt in range(max_retries):
        try:
            with db_lock():
                result = subprocess.run(f"python weekly_league.py process {challenge_id}", shell=True)
                if result.returncode == 0:
                    print(f"✅ Challenge {challenge_id} updated successfully")
                    return True
                else:
                    print(f"❌ Failed to update challenge {challenge_id} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        print(f"⏳ Retrying in 5 seconds...")
                        time.sleep(5)
        except Exception as e:
            print(f"❌ Database lock error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in 5 seconds...")
                time.sleep(5)
    
    print(f"❌ Failed to update challenge {challenge_id} after {max_retries} attempts")
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
