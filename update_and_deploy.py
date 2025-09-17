#!/usr/bin/env python3
"""
Update and Deploy Script

Automatically processes challenge results, commits changes, and pushes to GitHub.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_and_deploy.py <challenge_id>")
        print("\nExample:")
        print("  python update_and_deploy.py FbxiQzxzq9XuwwY2")
        sys.exit(1)
    
    challenge_id = sys.argv[1]
    
    print("🚀 GeoGuessr League - Update & Deploy")
    print("=" * 40)
    print(f"Challenge ID: {challenge_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Process challenge results
    if not run_command(f"python weekly_league.py process {challenge_id}", "Processing challenge results"):
        sys.exit(1)
    
    # Step 2: Add all changes to git
    if not run_command("git add .", "Adding changes to git"):
        sys.exit(1)
    
    # Step 3: Commit changes
    commit_message = f"Update results for challenge {challenge_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️  No changes to commit (maybe already up to date)")
    
    # Step 4: Push to GitHub
    if not run_command("git push", "Pushing to GitHub"):
        sys.exit(1)
    
    print()
    print("🎉 Update & Deploy completed successfully!")
    print()
    print("📱 Your dashboard will update automatically:")
    print("   Local: http://localhost:8501")
    print("   Deployed: https://karlsgeoliga.streamlit.app")
    print()
    print("💡 Next steps:")
    print("   - Check the dashboard for updated results")
    print("   - Close the challenge on Sunday: python weekly_league.py close " + challenge_id)

if __name__ == "__main__":
    main()
