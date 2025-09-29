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
from contextlib import contextmanager
from geoguessr_api import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database context manager to prevent locks
@contextmanager
def get_db_connection():
    """Get a database connection with proper cleanup."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
        conn.execute("PRAGMA journal_mode = WAL")    # Better concurrency
        yield conn
    finally:
        if conn:
            conn.close()

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
        with get_db_connection() as conn:
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
    
    def create_challenge(self, challenge_id: str, map_name: str = None, rounds: int = 5, time_limit: int = 0, end_date: datetime = None) -> bool:
        """Create a new challenge with optional custom end date."""
        week = self.get_current_week()
        start_date = datetime.now(TZ)
        
        # If no end_date provided, use current week's end date
        if end_date is None:
            _, end_date = self.get_week_dates(week)
        else:
            # Ensure end_date is timezone-aware
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=TZ)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Calculate status automatically based on end date
            current_time = datetime.now(TZ)
            status = 'active' if end_date > current_time else 'closed'
            
            cursor.execute('''
                INSERT OR REPLACE INTO challenges 
                (challenge_id, week, start_date, end_date, map_name, rounds, time_limit, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (challenge_id, week, start_date.date(), end_date.date(), map_name, rounds, time_limit, status))
            
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
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if challenge exists and get its info
                cursor.execute("SELECT challenge_id, week, end_date FROM challenges WHERE challenge_id = ?", (challenge_id,))
                challenge_info = cursor.fetchone()
                if not challenge_info:
                    return {"success": False, "message": "Challenge not found. Create it first."}
                
                challenge_week = challenge_info[1]
                challenge_end_date = datetime.strptime(challenge_info[2], '%Y-%m-%d').replace(tzinfo=TZ)
                current_time = datetime.now(TZ)
                
                new_players = 0
                updated_results = 0
                
                # First, collect all results and sort by score to calculate our own ranks
                results_with_scores = []
                for result in results:
                    player_id = result['userId']
                    player_name = result['username']
                    
                    # Check if player already has a result for this challenge
                    cursor.execute('''
                        SELECT result_id FROM player_results 
                        WHERE challenge_id = ? AND player_id = ?
                    ''', (challenge_id, player_id))
                    
                    if cursor.fetchone():
                        continue  # Skip if already exists (first attempt only)
                    
                    results_with_scores.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'score': result['totalScore'],
                        'distance': result['totalDistance'],
                        'time': result['totalTime'],
                        'countryCode': result.get('countryCode'),
                        'isVerified': result.get('isVerified', False)
                    })
                
                # Sort by score (descending) to calculate ranks
                results_with_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # Process each result with our calculated rank
                for i, result_data in enumerate(results_with_scores, 1):
                    player_id = result_data['player_id']
                    player_name = result_data['player_name']
                    
                    # Add/update player
                    cursor.execute('''
                        INSERT OR REPLACE INTO players 
                        (player_id, player_name, display_name, country_code, is_verified)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (player_id, player_name, player_name, result_data['countryCode'], result_data['isVerified']))
                    
                    # Add result with our calculated rank
                    cursor.execute('''
                        INSERT INTO player_results 
                        (challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (challenge_id, challenge_week, player_id, player_name, result_data['score'], 
                          result_data['distance'], result_data['time'], i))
                    
                    new_players += 1
                    updated_results += 1
                
                # If challenge is still active (before end_date), update standings immediately
                if current_time < challenge_end_date:
                    self._update_challenge_standings(challenge_id, challenge_week, conn, cursor)
                
                conn.commit()
            
            return {
                "success": True, 
                "message": f"Processed {updated_results} results, {new_players} new players"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error processing results: {e}"}
    
    def _update_challenge_standings(self, challenge_id: str, week: str, conn, cursor):
        """Update standings for a specific challenge."""
        # Get all results for this challenge, sorted by score (descending)
        cursor.execute('''
            SELECT player_id, player_name, score 
            FROM player_results 
            WHERE challenge_id = ? 
            ORDER BY score DESC
        ''', (challenge_id,))
        
        results = cursor.fetchall()
        
        # Calculate points and update weekly standings with our own ranking
        for rank, (player_id, player_name, score) in enumerate(results, 1):
            points = POINTS_SYSTEM.get(rank, 0)
            
            cursor.execute('''
                INSERT OR REPLACE INTO weekly_standings 
                (week, player_id, rank, score, points_awarded, participation)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (week, player_id, rank, score, points))
        
        # Update league standings
        self._update_league_standings(conn, cursor)
    
    def close_weekly_challenge(self, challenge_id: str) -> Dict:
        """Close a weekly challenge and calculate standings.
        
        DEPRECATED: Challenges now auto-close based on end_date.
        This method is kept for backward compatibility.
        """
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
    
    def _update_league_standings(self, conn=None, cursor=None):
        """Update overall league standings including active challenges."""
        if conn is None or cursor is None:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                self._update_league_standings(conn, cursor)
            return
        
        # Get all players and their stats from weekly_standings (closed challenges only)
        current_time = datetime.now(TZ)
        cursor.execute('''
            SELECT 
                p.player_id,
                COALESCE(SUM(ws.points_awarded), 0) as total_points,
                COUNT(ws.week) as total_challenges,
                MAX(ws.rank) as best_rank,
                MIN(ws.rank) as worst_rank
            FROM players p
            LEFT JOIN weekly_standings ws ON p.player_id = ws.player_id
            LEFT JOIN challenges c ON ws.week = c.week
            WHERE c.end_date < ? OR c.end_date IS NULL
            GROUP BY p.player_id
        ''', (current_time.date(),))
        
        # Store closed challenge stats
        closed_stats = {}
        for player_id, total_points, total_challenges, best_rank, worst_rank in cursor.fetchall():
            closed_stats[player_id] = {
                'total_points': total_points,
                'total_challenges': total_challenges,
                'best_rank': best_rank,
                'worst_rank': worst_rank
            }
        
        # Get active challenges and their current standings
        cursor.execute('''
            SELECT DISTINCT c.challenge_id, c.week, c.end_date
            FROM challenges c
            WHERE c.status = 'active' AND c.end_date > ?
        ''', (current_time.date(),))
        
        active_challenges = cursor.fetchall()
        
        # For each active challenge, get current standings
        for challenge_id, week, end_date in active_challenges:
            cursor.execute('''
                SELECT player_id, score
                FROM player_results 
                WHERE challenge_id = ? 
                ORDER BY score DESC
            ''', (challenge_id,))
            
            results = cursor.fetchall()
            
            # Calculate points for this challenge using our own ranking
            for rank, (player_id, score) in enumerate(results, 1):
                points = POINTS_SYSTEM.get(rank, 0)
                
                # Initialize player stats if not exists
                if player_id not in closed_stats:
                    closed_stats[player_id] = {
                        'total_points': 0,
                        'total_challenges': 0,
                        'best_rank': None,
                        'worst_rank': None
                    }
                
                # Add points from this active challenge
                closed_stats[player_id]['total_points'] += points
                closed_stats[player_id]['total_challenges'] += 1
                
                # Update best/worst ranks
                if closed_stats[player_id]['best_rank'] is None or rank < closed_stats[player_id]['best_rank']:
                    closed_stats[player_id]['best_rank'] = rank
                if closed_stats[player_id]['worst_rank'] is None or rank > closed_stats[player_id]['worst_rank']:
                    closed_stats[player_id]['worst_rank'] = rank
        
        # Update league standings with combined stats
        for player_id, stats in closed_stats.items():
            cursor.execute('''
                INSERT OR REPLACE INTO league_standings 
                (player_id, total_points, total_challenges, best_rank, worst_rank, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (player_id, stats['total_points'], stats['total_challenges'], 
                  stats['best_rank'], stats['worst_rank']))
        
        conn.commit()
    
    def get_active_challenges(self) -> List[Dict]:
        """Get all active challenges with their end dates."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        current_time = datetime.now(TZ)
        cursor.execute('''
            SELECT challenge_id, week, start_date, end_date, map_name, status
            FROM challenges 
            WHERE status = 'active' AND end_date > ?
            ORDER BY start_date DESC
        ''', (current_time.date(),))
        
        challenges = []
        for row in cursor.fetchall():
            challenges.append({
                'challenge_id': row[0],
                'week': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'map_name': row[4],
                'status': row[5]
            })
        
        conn.close()
        return challenges
    
    def update_challenge_end_date(self, challenge_id: str, new_end_date: datetime) -> Dict:
        """Update the end date of an existing challenge."""
        # Ensure end_date is timezone-aware
        if new_end_date.tzinfo is None:
            new_end_date = new_end_date.replace(tzinfo=TZ)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Check if challenge exists
            cursor.execute("SELECT challenge_id FROM challenges WHERE challenge_id = ?", (challenge_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Challenge not found"}
            
            # Update end_date
            cursor.execute('''
                UPDATE challenges 
                SET end_date = ?
                WHERE challenge_id = ?
            ''', (new_end_date.date(), challenge_id))
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Challenge {challenge_id} end date updated to {new_end_date.strftime('%Y-%m-%d %H:%M')} CET"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error updating end date: {e}"}
        finally:
            conn.close()
    
    def update_all_challenge_statuses(self):
        """Update all challenge statuses based on current time and end dates."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now(TZ)
            
            # Update all challenges based on their end dates
            cursor.execute('''
                UPDATE challenges 
                SET status = CASE 
                    WHEN end_date > ? THEN 'active'
                    ELSE 'closed'
                END
            ''', (current_time.date(),))
            
            conn.commit()
            
            # Get count of updated challenges
            cursor.execute("SELECT COUNT(*) FROM challenges")
            total_challenges = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM challenges WHERE status = 'active'")
            active_challenges = cursor.fetchone()[0]
            
            return {
                "success": True,
                "message": f"Updated {total_challenges} challenges: {active_challenges} active, {total_challenges - active_challenges} closed"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error updating statuses: {e}"}
        finally:
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
