#!/usr/bin/env python3
"""
Super Simple Update Script

Just run: python update.py CHALLENGE_ID
"""

import sys
import subprocess

if len(sys.argv) < 2:
    print("Usage: python update.py <challenge_id>")
    sys.exit(1)

challenge_id = sys.argv[1]

print(f"🚀 Updating challenge {challenge_id}...")

# Process results
subprocess.run(f"python weekly_league.py process {challenge_id}", shell=True)

# Add, commit, push
subprocess.run("git add .", shell=True)
subprocess.run(f'git commit -m "Update results for {challenge_id}"', shell=True)
subprocess.run("git push", shell=True)

print("✅ Done! Dashboard updated.")
