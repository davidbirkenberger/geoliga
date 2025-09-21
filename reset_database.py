#!/usr/bin/env python3
"""
Reset GeoGuessr League Database

This script clears all data from the database to start fresh.
"""

import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

def reset_database():
    """Reset the database by clearing all data."""
    db_path = "geoliga.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    # Create backup first
    backup_path = f"geoliga_backup_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.db"
    print(f"📦 Creating backup: {backup_path}")
    
    try:
        # Copy database to backup
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🗑️  Clearing all data...")
        
        # Clear all tables (in correct order due to foreign keys)
        tables_to_clear = [
            'league_standings',
            'weekly_standings', 
            'player_results',
            'challenges',
            'players'
        ]
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   ✅ Cleared {table}")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence")
        
        # Commit changes
        conn.commit()
        
        print("✅ Database reset successfully!")
        print("📊 All tables are now empty and ready for new data.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🔄 GeoGuessr League Database Reset")
    print("=" * 40)
    
    # Confirm reset
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("📦 A backup will be created before clearing.")
    
    confirm = input("\nAre you sure you want to reset? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        if reset_database():
            print("\n🎉 Database reset complete!")
            print("🚀 You can now start fresh with new challenges.")
        else:
            print("\n❌ Database reset failed!")
    else:
        print("❌ Reset cancelled.")

if __name__ == "__main__":
    main()
