#!/usr/bin/env python3
"""
GeoGuessr League Dashboard - Simple Version (No Plotly)

A simple Streamlit dashboard for tracking weekly GeoGuessr league standings.
This version doesn't require Plotly and should work on all platforms.
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configuration
TZ = ZoneInfo("Europe/Berlin")
DB_PATH = "geoliga.db"

# Page config
st.set_page_config(
    page_title="GeoGuessr League",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def get_league_standings():
    """Get overall league standings."""
    conn = get_db_connection()
    query = """
        SELECT 
            ls.total_points,
            p.player_name,
            ls.total_challenges,
            ls.best_rank,
            ls.worst_rank,
            ls.last_updated
        FROM league_standings ls
        JOIN players p ON ls.player_id = p.player_id
        ORDER BY ls.total_points DESC, ls.best_rank ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_weekly_standings(week=None):
    """Get weekly standings for a specific week."""
    conn = get_db_connection()
    
    if week is None:
        # Get current week
        now = datetime.now(TZ)
        week = now.strftime("%Y-W%U")
    
    query = """
        SELECT 
            ws.rank,
            p.player_name,
            ws.score,
            ws.points_awarded,
            pr.distance_km,
            pr.time_seconds
        FROM weekly_standings ws
        JOIN players p ON ws.player_id = p.player_id
        JOIN player_results pr ON ws.player_id = pr.player_id AND ws.week = pr.week
        WHERE ws.week = ? AND ws.participation = 1
        ORDER BY ws.rank
    """
    df = pd.read_sql_query(query, conn, params=(week,))
    conn.close()
    return df

def get_available_weeks():
    """Get list of available weeks."""
    conn = get_db_connection()
    query = "SELECT DISTINCT week FROM weekly_standings ORDER BY week DESC"
    weeks = pd.read_sql_query(query, conn)['week'].tolist()
    conn.close()
    return weeks

def format_time(seconds):
    """Format seconds as MM:SS."""
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def main():
    # Header
    st.title("🌍 GeoGuessr League Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("📊 Navigation")
    
    # Check if database exists
    try:
        conn = get_db_connection()
        conn.close()
    except:
        st.error("❌ Database not found! Please run the league manager first.")
        st.stop()
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏆 League Standings", "📅 Weekly Results", "👥 Player Stats"]
    )
    
    if page == "🏆 League Standings":
        show_league_standings()
    elif page == "📅 Weekly Results":
        show_weekly_results()
    elif page == "👥 Player Stats":
        show_player_stats()

def show_league_standings():
    """Display overall league standings."""
    st.header("🏆 League Standings")
    
    df = get_league_standings()
    
    if df.empty:
        st.warning("No league data available yet!")
        return
    
    # Create a nice table
    df_display = df.copy()
    df_display['rank'] = range(1, len(df_display) + 1)
    df_display = df_display[['rank', 'player_name', 'total_points', 'total_challenges', 'best_rank', 'worst_rank']]
    df_display.columns = ['Rank', 'Player', 'Total Points', 'Challenges', 'Best Rank', 'Worst Rank']
    
    # Display table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(df))
    with col2:
        st.metric("Total Challenges", df['total_challenges'].sum())
    with col3:
        st.metric("Highest Score", f"{df['total_points'].max()} pts")
    with col4:
        st.metric("Most Active", df.loc[df['total_challenges'].idxmax(), 'player_name'])

def show_weekly_results():
    """Display weekly results."""
    st.header("📅 Weekly Results")
    
    weeks = get_available_weeks()
    if not weeks:
        st.warning("No weekly data available yet!")
        return
    
    # Week selector
    selected_week = st.selectbox("Select Week:", weeks)
    
    df = get_weekly_standings(selected_week)
    
    if df.empty:
        st.warning(f"No data for week {selected_week}")
        return
    
    # Display results
    df_display = df.copy()
    df_display['time_formatted'] = df_display['time_seconds'].apply(format_time)
    df_display = df_display[['rank', 'player_name', 'score', 'points_awarded', 'distance_km', 'time_formatted']]
    df_display.columns = ['Rank', 'Player', 'Score', 'League Points', 'Distance (km)', 'Time']
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Week summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Participants", len(df))
    with col2:
        st.metric("Highest Score", f"{df['score'].max():,}")
    with col3:
        st.metric("Best Time", format_time(df['time_seconds'].min()))

def show_player_stats():
    """Display detailed player statistics."""
    st.header("👥 Player Statistics")
    
    # Get all players
    conn = get_db_connection()
    query = """
        SELECT 
            p.player_name,
            ls.total_points,
            ls.total_challenges,
            ls.best_rank,
            ls.worst_rank,
            COUNT(pr.result_id) as total_attempts,
            AVG(pr.score) as avg_score,
            AVG(pr.distance_km) as avg_distance,
            AVG(pr.time_seconds) as avg_time
        FROM players p
        LEFT JOIN league_standings ls ON p.player_id = ls.player_id
        LEFT JOIN player_results pr ON p.player_id = pr.player_id
        GROUP BY p.player_id, p.player_name
        ORDER BY ls.total_points DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.warning("No player data available yet!")
        return
    
    # Player selector
    player = st.selectbox("Select Player:", df['player_name'].tolist())
    
    player_data = df[df['player_name'] == player].iloc[0]
    
    # Player overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Points", f"{player_data['total_points']:.0f}")
    with col2:
        st.metric("Challenges Played", f"{player_data['total_challenges']:.0f}")
    with col3:
        st.metric("Best Rank", f"#{player_data['best_rank']:.0f}")
    with col4:
        st.metric("Worst Rank", f"#{player_data['worst_rank']:.0f}")
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Score", f"{player_data['avg_score']:.0f}")
    with col2:
        st.metric("Average Distance", f"{player_data['avg_distance']:.1f} km")
    with col3:
        st.metric("Average Time", format_time(player_data['avg_time']))

if __name__ == "__main__":
    main()
