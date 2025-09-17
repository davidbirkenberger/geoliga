#!/usr/bin/env python3
"""
Create a demo database with sample data for Streamlit Cloud deployment.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

def create_demo_database():
    """Create a demo database with sample data."""
    
    # Remove existing demo database
    if os.path.exists("geoliga_demo.db"):
        os.remove("geoliga_demo.db")
    
    conn = sqlite3.connect("geoliga_demo.db")
    cursor = conn.cursor()
    
    # Create tables
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
    
    # Insert demo data
    demo_players = [
        ("player1", "Geosky", "Geosky", "ro", 0),
        ("player2", "Chinker", "Chinker", "us", 0),
        ("player3", "Gat15", "Gat15", "es", 0),
        ("player4", "TheFlane34", "TheFlane34", "it", 0),
        ("player5", "m1r", "m1r", "ru", 0),
        ("player6", "pxeliasxt", "pxeliasxt", "de", 0),
        ("player7", "EnchantingSummit973", "EnchantingSummit973", "qa", 0),
        ("player8", "InfiniteDune090", "InfiniteDune090", "bg", 0),
        ("player9", "HillyStatue375", "HillyStatue375", "tr", 0),
        ("player10", "EquatorialGulf415", "EquatorialGulf415", "ph", 0),
    ]
    
    for player_id, player_name, display_name, country_code, is_verified in demo_players:
        cursor.execute('''
            INSERT INTO players (player_id, player_name, display_name, country_code, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, player_name, display_name, country_code, is_verified))
    
    # Insert demo challenge
    cursor.execute('''
        INSERT INTO challenges (challenge_id, week, start_date, end_date, map_name, rounds, time_limit, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("demo_challenge", "2025-W37", "2025-09-15", "2025-09-21", "A Community World", 5, 0, "closed"))
    
    # Insert demo results for current week (pending)
    current_week = datetime.now(TZ).strftime("%Y-W%U")
    demo_results = [
        ("demo_challenge", current_week, "player1", "Geosky", 15335, 15905.3, 1077, 1),
        ("demo_challenge", current_week, "player2", "Chinker", 13464, 7731.9, 82479, 2),
        ("demo_challenge", current_week, "player3", "Gat15", 11739, 8568.4, 258, 3),
        ("demo_challenge", current_week, "player4", "TheFlane34", 9888, 10440.7, 115, 4),
        ("demo_challenge", current_week, "player5", "m1r", 9604, 16345.3, 318, 5),
        ("demo_challenge", current_week, "player6", "pxeliasxt", 9182, 38519.5, 479, 6),
        ("demo_challenge", current_week, "player7", "EnchantingSummit973", 6957, 29998.9, 160, 7),
        ("demo_challenge", current_week, "player8", "InfiniteDune090", 6909, 34660.5, 230, 8),
        ("demo_challenge", current_week, "player9", "HillyStatue375", 6873, 18273.5, 228, 9),
        ("demo_challenge", current_week, "player10", "EquatorialGulf415", 6293, 24097.3, 816, 10),
    ]
    
    # Also add a previous week (closed)
    prev_week = (datetime.now(TZ) - timedelta(weeks=1)).strftime("%Y-W%U")
    prev_results = [
        ("demo_challenge_prev", prev_week, "player1", "Geosky", 14200, 12000.0, 900, 1),
        ("demo_challenge_prev", prev_week, "player2", "Chinker", 13800, 15000.0, 1200, 2),
        ("demo_challenge_prev", prev_week, "player3", "Gat15", 12500, 18000.0, 800, 3),
        ("demo_challenge_prev", prev_week, "player4", "TheFlane34", 11000, 20000.0, 1000, 4),
        ("demo_challenge_prev", prev_week, "player5", "m1r", 9500, 25000.0, 600, 5),
    ]
    
    for challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank in demo_results:
        cursor.execute('''
            INSERT INTO player_results (challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank))
    
    # Insert weekly standings
    points_system = {1: 25, 2: 20, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    
    for challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank in demo_results:
        points = points_system.get(rank, 0)
        cursor.execute('''
            INSERT INTO weekly_standings (week, player_id, rank, score, points_awarded, participation)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (week, player_id, rank, score, points))
    
    # Insert league standings
    for challenge_id, week, player_id, player_name, score, distance_km, time_seconds, rank in demo_results:
        points = points_system.get(rank, 0)
        cursor.execute('''
            INSERT INTO league_standings (player_id, total_points, total_challenges, best_rank, worst_rank)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, points, 1, rank, rank))
    
    conn.commit()
    conn.close()
    
    print("✅ Demo database created successfully!")
    print("📊 Contains 10 demo players with sample data")
    print("🏆 Ready for Streamlit Cloud deployment")

if __name__ == "__main__":
    create_demo_database()
