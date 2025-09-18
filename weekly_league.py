#!/usr/bin/env python3
"""
Weekly GeoGuessr League - Simple Command Line Interface

Usage:
    python weekly_league.py create <challenge_id> [map_name] [end_date]
    python weekly_league.py process <challenge_id>
    python weekly_league.py close <challenge_id>
    python weekly_league.py standings [week]
    python weekly_league.py league
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from league_manager import LeagueManager

TZ = ZoneInfo("Europe/Berlin")

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    league = LeagueManager()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: python weekly_league.py create <challenge_id> [map_name] [end_date]")
            print("end_date format: YYYY-MM-DD (e.g., 2024-01-15)")
            sys.exit(1)
        
        challenge_id = sys.argv[2]
        map_name = sys.argv[3] if len(sys.argv) > 3 else None
        end_date = None
        
        # Parse end_date if provided
        if len(sys.argv) > 4:
            try:
                end_date = datetime.strptime(sys.argv[4], '%Y-%m-%d').replace(tzinfo=TZ)
            except ValueError:
                print("❌ Invalid end_date format. Use YYYY-MM-DD (e.g., 2024-01-15)")
                sys.exit(1)
        
        result = league.create_challenge(challenge_id, map_name, end_date=end_date)
        if result:
            if end_date:
                print(f"✅ Challenge {challenge_id} created for week {league.get_current_week()}")
                print(f"📅 Challenge ends: {end_date.strftime('%Y-%m-%d %H:%M')} CET")
            else:
                print(f"✅ Challenge {challenge_id} created for week {league.get_current_week()}")
                print("📅 Challenge ends: End of current week")
        else:
            print("❌ Failed to create challenge")
    
    elif command == "process":
        if len(sys.argv) < 3:
            print("Usage: python weekly_league.py process <challenge_id>")
            sys.exit(1)
        
        challenge_id = sys.argv[2]
        result = league.process_challenge_results(challenge_id)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
    
    elif command == "close":
        if len(sys.argv) < 3:
            print("Usage: python weekly_league.py close <challenge_id>")
            sys.exit(1)
        
        challenge_id = sys.argv[2]
        result = league.close_weekly_challenge(challenge_id)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
        if result['success']:
            print("\n" + "="*50)
            print("📱 WEEKLY STANDINGS - COPY TO WHATSAPP:")
            print("="*50)
            print(league.format_weekly_standings())
            print("="*50)
    
    elif command == "standings":
        week = sys.argv[2] if len(sys.argv) > 2 else None
        message = league.format_weekly_standings(week)
        print("\n" + "="*50)
        print("📱 COPY TO WHATSAPP:")
        print("="*50)
        print(message)
        print("="*50)
    
    elif command == "league":
        message = league.format_league_standings()
        print("\n" + "="*50)
        print("📱 COPY TO WHATSAPP:")
        print("="*50)
        print(message)
        print("="*50)
    
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)

def print_usage():
    print("🏆 Weekly GeoGuessr League Manager")
    print("=" * 40)
    print("Commands:")
    print("  create <challenge_id> [map_name] [end_date]  - Create new challenge")
    print("  process <challenge_id>                       - Process challenge results")
    print("  close <challenge_id>                         - Close weekly challenge")
    print("  standings [week]                             - Show weekly standings")
    print("  league                                       - Show overall league standings")
    print("\nExamples:")
    print("  python weekly_league.py create FbxiQzxzq9XuwwY2 'A Community World'")
    print("  python weekly_league.py create FbxiQzxzq9XuwwY2 'A Community World' 2024-01-15")
    print("  python weekly_league.py process FbxiQzxzq9XuwwY2")
    print("  python weekly_league.py close FbxiQzxzq9XuwwY2")
    print("  python weekly_league.py standings")
    print("  python weekly_league.py league")
    print("\nNote: Challenges now count directly into overall standings while active!")
    print("      Set end_date to control when challenge stops accepting new entries.")

if __name__ == "__main__":
    main()
