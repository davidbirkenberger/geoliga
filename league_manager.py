#!/usr/bin/env python3
"""
GeoGuessr League Manager

Manages a weekly GeoGuessr league with rank-based scoring.
Tracks only the first attempt per player per week.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Tuple
from geoguessr_api import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TZ = ZoneInfo("Europe/Berlin")
DB_PATH = "geoliga.db"

# Get cookies from environment variables
NCFA_COOKIE = os.getenv('NCFA_COOKIE')
SESSION_COOKIE = os.getenv('SESSION_COOKIE')
GG_TOKEN = os.getenv('GG_TOKEN')

# Validate that cookies are loaded
if not all([NCFA_COOKIE, SESSION_COOKIE, GG_TOKEN]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# Points system (rank-based)
POINTS_SYSTEM = {
    1: 25, 2: 20, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}


class LeagueManager:
    """Manages the GeoGuessr league database and operations."""
    
    def __init__(self):
        self.init_database()
        self.client = create_client(NCFA_COOKIE, SESSION_COOKIE, GG_TOKEN)
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Challenges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id TEXT PRIMARY KEY,
                week TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                map_name TEXT,
                rounds INTEGER,
                time_limit INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                player_name TEXT NOT NULL,
                display_name TEXT,
                country_code TEXT,
                is_verified BOOLEAN DEFAULT 0,
                joined_league DATE DEFAULT CURRENT_DATE,
                total_challenges_played INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_weekly_rank INTEGER,
                total_league_points INTEGER DEFAULT 0
            )
        ''')
        
        # Player results table (first attempt only)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT NOT NULL,
                week TEXT NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                time_seconds INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (challenge_id) REFERENCES challenges (challenge_id),
                FOREIGN KEY (player_id) REFERENCES players (player_id),
                UNIQUE (challenge_id, player_id)
            )
        ''')
        
        # Weekly standings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_standings (
                week TEXT NOT NULL,
                player_id TEXT NOT NULL,
                rank INTEGER NOT NULL,
                score INTEGER NOT NULL,
                points_awarded INTEGER NOT NULL,
                participation BOOLEAN DEFAULT 1,
                PRIMARY KEY (week, player_id),
                FOREIGN KEY (player_id) REFERENCES players (player_id)
            )
        ''')
        
        # League standings table (overall)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS league_standings (
                player_id TEXT PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                total_challenges INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_rank INTEGER,
                worst_rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (player_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_current_week(self) -> str:
        """Get current week in YYYY-W## format."""
        now = datetime.now(TZ)
        return now.strftime("%Y-W%U")
    
    def get_week_dates(self, week: str) -> Tuple[datetime, datetime]:
        """Get start and end dates for a given week."""
        year, week_num = week.split('-W')
        year, week_num = int(year), int(week_num)
        
        # Get first Monday of the year
        jan1 = datetime(year, 1, 1, tzinfo=TZ)
        days_to_monday = (7 - jan1.weekday()) % 7
        if days_to_monday == 0 and jan1.weekday() != 0:
            days_to_monday = 7
        first_monday = jan1 + timedelta(days=days_to_monday)
        
        # Calculate the Monday of the target week
        target_monday = first_monday + timedelta(weeks=week_num - 1)
        target_sunday = target_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return target_monday, target_sunday
    
    def create_challenge(self, challenge_id: str, map_name: str = None, rounds: int = 5, time_limit: int = 0) -> bool:
        """Create a new challenge for the current week."""
        week = self.get_current_week()
        start_date, end_date = self.get_week_dates(week)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO challenges 
                (challenge_id, week, start_date, end_date, map_name, rounds, time_limit, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (challenge_id, week, start_date.date(), end_date.date(), map_name, rounds, time_limit))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating challenge: {e}")
            return False
        finally:
            conn.close()
    
    def process_challenge_results(self, challenge_id: str) -> Dict:
        """Process results for a challenge and update database."""
        try:
            # Get results from GeoGuessr API
            results = self.client.get_challenge_leaderboard(challenge_id, friends_only=False, limit=50)
            
            if not results:
                return {"success": False, "message": "No results found"}
            
            week = self.get_current_week()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if challenge exists
            cursor.execute("SELECT challenge_id FROM challenges WHERE challenge_id = ?", (challenge_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Challenge not found. Create it first."}
            
            new_players = 0
            updated_results = 0
            
            for i, result in enumerate(results, 1):
                player_id = result['userId']
                player_name = result['username']
                
                # Check if player already has a result for this challenge
                cursor.execute('''
                    SELECT result_id FROM player_results 
                    WHERE challenge_id = ? AND player_id = ?
                ''', (challenge_id, player_id))
                
                if cursor.fetchone():
                    continue  # Skip if already exists (first attempt only)
                
                # Add/update player
                cursor.execute('''
                    INSERT OR REPLACE INTO players 
                    (player_id, player_name, display_name, country_code, is_verified)
                    VALUES (?, ?, ?, ?, ?)
                ''', (player_id, player_name, player_name, result.get('countryCode'), result.get('isVerified', False)))
                
                # Add result
                cursor.execute('''
                    INSERT INTO player_results 
                    (challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (challenge_id, week, player_id, player_name, result['totalScore'], 
                      result['totalDistance'], result['totalTime'], i))
                
                new_players += 1
                updated_results += 1
            
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "message": f"Processed {updated_results} results, {new_players} new players"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error processing results: {e}"}
    
    def close_weekly_challenge(self, challenge_id: str) -> Dict:
        """Close a weekly challenge and calculate standings."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Get challenge info
            cursor.execute("SELECT week FROM challenges WHERE challenge_id = ?", (challenge_id,))
            result = cursor.fetchone()
            if not result:
                return {"success": False, "message": "Challenge not found"}
            
            week = result[0]
            
            # Get all results for this challenge, sorted by rank
            cursor.execute('''
                SELECT player_id, player_name, score, rank 
                FROM player_results 
                WHERE challenge_id = ? 
                ORDER BY rank
            ''', (challenge_id,))
            
            results = cursor.fetchall()
            
            # Calculate points and update weekly standings
            for player_id, player_name, score, rank in results:
                points = POINTS_SYSTEM.get(rank, 0)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO weekly_standings 
                    (week, player_id, rank, score, points_awarded, participation)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (week, player_id, rank, score, points))
            
            # Update challenge status
            cursor.execute('''
                UPDATE challenges SET status = 'closed' WHERE challenge_id = ?
            ''', (challenge_id,))
            
            # Update league standings
            self._update_league_standings()
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Weekly challenge closed. {len(results)} players participated."
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error closing challenge: {e}"}
        finally:
            conn.close()
    
    def _update_league_standings(self):
        """Update overall league standings."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all players and their stats
        cursor.execute('''
            SELECT 
                p.player_id,
                COALESCE(SUM(ws.points_awarded), 0) as total_points,
                COUNT(ws.week) as total_challenges,
                MAX(ws.rank) as best_rank,
                MIN(ws.rank) as worst_rank
            FROM players p
            LEFT JOIN weekly_standings ws ON p.player_id = ws.player_id
            GROUP BY p.player_id
        ''')
        
        for player_id, total_points, total_challenges, best_rank, worst_rank in cursor.fetchall():
            cursor.execute('''
                INSERT OR REPLACE INTO league_standings 
                (player_id, total_points, total_challenges, best_rank, worst_rank, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (player_id, total_points, total_challenges, best_rank, worst_rank))
        
        conn.commit()
        conn.close()
    
    def get_weekly_standings(self, week: str = None) -> List[Dict]:
        """Get standings for a specific week."""
        if week is None:
            week = self.get_current_week()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ws.rank, p.player_name, ws.score, ws.points_awarded
            FROM weekly_standings ws
            JOIN players p ON ws.player_id = p.player_id
            WHERE ws.week = ? AND ws.participation = 1
            ORDER BY ws.rank
        ''', (week,))
        
        results = []
        for rank, player_name, score, points in cursor.fetchall():
            results.append({
                'rank': rank,
                'player_name': player_name,
                'score': score,
                'points': points
            })
        
        conn.close()
        return results
    
    def get_league_standings(self) -> List[Dict]:
        """Get overall league standings."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ls.total_points,
                p.player_name,
                ls.total_challenges,
                ls.best_rank,
                ls.worst_rank
            FROM league_standings ls
            JOIN players p ON ls.player_id = p.player_id
            ORDER BY ls.total_points DESC, ls.best_rank ASC
        ''')
        
        results = []
        for i, (total_points, player_name, total_challenges, best_rank, worst_rank) in enumerate(cursor.fetchall(), 1):
            results.append({
                'rank': i,
                'player_name': player_name,
                'total_points': total_points,
                'total_challenges': total_challenges,
                'best_rank': best_rank,
                'worst_rank': worst_rank
            })
        
        conn.close()
        return results
    
    def format_weekly_standings(self, week: str = None) -> str:
        """Format weekly standings as a message."""
        standings = self.get_weekly_standings(week)
        
        if not standings:
            return f"🏆 **Week {week or self.get_current_week()} Standings**\n\nNo results yet!"
        
        lines = [f"🏆 **Week {week or self.get_current_week()} Standings**", ""]
        
        for standing in standings:
            lines.append(f"{standing['rank']}. **{standing['player_name']}** — {standing['score']:,} pts ({standing['points']} league points)")
        
        return "\n".join(lines)
    
    def format_league_standings(self) -> str:
        """Format overall league standings as a message."""
        standings = self.get_league_standings()
        
        if not standings:
            return "🏆 **League Standings**\n\nNo players yet!"
        
        lines = ["🏆 **League Standings**", ""]
        
        for standing in standings[:10]:  # Top 10
            lines.append(f"{standing['rank']}. **{standing['player_name']}** — {standing['total_points']} pts ({standing['total_challenges']} challenges)")
        
        if len(standings) > 10:
            lines.append(f"\n... and {len(standings) - 10} more players")
        
        return "\n".join(lines)


def main():
    """Interactive mode for testing."""
    league = LeagueManager()
    
    print("🏆 GeoGuessr League Manager")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Create new challenge")
        print("2. Process challenge results")
        print("3. Close weekly challenge")
        print("4. View weekly standings")
        print("5. View league standings")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            challenge_id = input("Enter challenge ID: ").strip()
            map_name = input("Enter map name (optional): ").strip() or None
            result = league.create_challenge(challenge_id, map_name)
            print("✅ Challenge created!" if result else "❌ Failed to create challenge")
            
        elif choice == "2":
            challenge_id = input("Enter challenge ID: ").strip()
            result = league.process_challenge_results(challenge_id)
            print(f"{'✅' if result['success'] else '❌'} {result['message']}")
            
        elif choice == "3":
            challenge_id = input("Enter challenge ID: ").strip()
            result = league.close_weekly_challenge(challenge_id)
            print(f"{'✅' if result['success'] else '❌'} {result['message']}")
            
        elif choice == "4":
            week = input("Enter week (YYYY-W##) or press Enter for current: ").strip() or None
            message = league.format_weekly_standings(week)
            print("\n" + "="*50)
            print("📱 COPY TO WHATSAPP:")
            print("="*50)
            print(message)
            print("="*50)
            
        elif choice == "5":
            message = league.format_league_standings()
            print("\n" + "="*50)
            print("📱 COPY TO WHATSAPP:")
            print("="*50)
            print(message)
            print("="*50)
            
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
