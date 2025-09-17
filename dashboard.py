#!/usr/bin/env python3
"""
GeoGuessr League Dashboard

A beautiful Streamlit dashboard for tracking weekly GeoGuessr league standings.
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Try to import plotly, fallback to simple version if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Using simple charts.")

# Configuration
TZ = ZoneInfo("Europe/Berlin")
# Always use main database for local development
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
    
    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='league_standings'")
    if not cursor.fetchone():
        conn.close()
        return pd.DataFrame()
    
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
    
    # Check which tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    df = pd.DataFrame()
    
    # First try to get from weekly_standings (closed challenges)
    if 'weekly_standings' in tables and 'players' in tables and 'player_results' in tables:
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
        try:
            df = pd.read_sql_query(query, conn, params=(week,))
        except:
            df = pd.DataFrame()
    
    # If no closed standings, get pending results from player_results
    if df.empty and 'player_results' in tables:
        query_pending = """
            SELECT 
                pr.rank,
                pr.player_name,
                pr.score,
                0 as points_awarded,
                pr.distance_km,
                pr.time_seconds
            FROM player_results pr
            WHERE pr.week = ?
            ORDER BY pr.rank
        """
        try:
            df = pd.read_sql_query(query_pending, conn, params=(week,))
        except:
            df = pd.DataFrame()
    
    conn.close()
    return df

def get_available_weeks():
    """Get list of available weeks."""
    conn = get_db_connection()
    
    # Check which tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    weeks = []
    
    # Get weeks from weekly_standings if it exists
    if 'weekly_standings' in tables:
        query = "SELECT DISTINCT week FROM weekly_standings"
        try:
            weeks.extend(pd.read_sql_query(query, conn)['week'].tolist())
        except:
            pass
    
    # Get weeks from player_results if it exists
    if 'player_results' in tables:
        query = "SELECT DISTINCT week FROM player_results"
        try:
            weeks.extend(pd.read_sql_query(query, conn)['week'].tolist())
        except:
            pass
    
    # Remove duplicates and sort
    weeks = sorted(list(set(weeks)), reverse=True)
    conn.close()
    return weeks

def get_player_stats():
    """Get detailed player statistics."""
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
    return df

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
        ["🏆 League Standings", "📅 Weekly Results", "👥 Player Stats", "📈 Analytics"]
    )
    
    if page == "🏆 League Standings":
        show_league_standings()
    elif page == "📅 Weekly Results":
        show_weekly_results()
    elif page == "👥 Player Stats":
        show_player_stats()
    elif page == "📈 Analytics":
        show_analytics()

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
    
    # Highlight top 3
    def highlight_top3(row):
        if row['Rank'] == 1:
            return ['background-color: #FFD700'] * len(row)  # Gold
        elif row['Rank'] == 2:
            return ['background-color: #C0C0C0'] * len(row)  # Silver
        elif row['Rank'] == 3:
            return ['background-color: #CD7F32'] * len(row)  # Bronze
        else:
            return [''] * len(row)
    
    st.dataframe(
        df_display.style.apply(highlight_top3, axis=1),
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
    
    # Check if this is pending results (no league points awarded yet)
    is_pending = df['points_awarded'].sum() == 0
    
    # Display status
    if is_pending:
        st.info("🔄 **Live Results** - Challenge is still active. League points will be awarded when the week closes.")
    else:
        st.success("✅ **Final Results** - Week has been closed and league points awarded.")
    
    # Display results
    df_display = df.copy()
    df_display['time_formatted'] = df_display['time_seconds'].apply(format_time)
    df_display = df_display[['rank', 'player_name', 'score', 'points_awarded', 'distance_km', 'time_formatted']]
    df_display.columns = ['Rank', 'Player', 'Score', 'League Points', 'Distance (km)', 'Time']
    
    # Highlight top 3
    def highlight_top3(row):
        if row['Rank'] == 1:
            return ['background-color: #FFD700'] * len(row)
        elif row['Rank'] == 2:
            return ['background-color: #C0C0C0'] * len(row)
        elif row['Rank'] == 3:
            return ['background-color: #CD7F32'] * len(row)
        else:
            return [''] * len(row)
    
    st.dataframe(
        df_display.style.apply(highlight_top3, axis=1),
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
    
    # Show additional info for pending results
    if is_pending:
        st.info("💡 **Tip**: Use `python weekly_league.py process CHALLENGE_ID` to update results during the week!")

def show_player_stats():
    """Display detailed player statistics."""
    st.header("👥 Player Statistics")
    
    df = get_player_stats()
    
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

def show_analytics():
    """Display analytics and charts."""
    st.header("📈 Analytics")
    
    df_league = get_league_standings()
    df_players = get_player_stats()
    
    if df_league.empty:
        st.warning("No data available for analytics!")
        return
    
    if PLOTLY_AVAILABLE:
        # Points distribution
        st.subheader("Points Distribution")
        fig = px.bar(
            df_league.head(10), 
            x='player_name', 
            y='total_points',
            title="Top 10 Players by Points",
            color='total_points',
            color_continuous_scale='viridis'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Participation chart
        st.subheader("Participation Rate")
        participation_data = df_players[df_players['total_challenges'] > 0].copy()
        participation_data['participation_rate'] = (participation_data['total_challenges'] / participation_data['total_challenges'].max()) * 100
        
        fig = px.scatter(
            participation_data,
            x='total_challenges',
            y='total_points',
            size='avg_score',
            hover_data=['player_name'],
            title="Participation vs Performance",
            labels={'total_challenges': 'Challenges Played', 'total_points': 'Total Points'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance trends
        st.subheader("Performance Trends")
        
        # Get weekly data for trends
        weeks = get_available_weeks()
        if len(weeks) > 1:
            trend_data = []
            for week in weeks:
                week_df = get_weekly_standings(week)
                if not week_df.empty:
                    trend_data.append({
                        'week': week,
                        'participants': len(week_df),
                        'avg_score': week_df['score'].mean(),
                        'best_score': week_df['score'].max()
                    })
            
            if trend_data:
                trend_df = pd.DataFrame(trend_data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trend_df['week'],
                    y=trend_df['participants'],
                    mode='lines+markers',
                    name='Participants',
                    yaxis='y'
                ))
                fig.add_trace(go.Scatter(
                    x=trend_df['week'],
                    y=trend_df['avg_score'],
                    mode='lines+markers',
                    name='Average Score',
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title="Weekly Trends",
                    xaxis_title="Week",
                    yaxis=dict(title="Participants", side="left"),
                    yaxis2=dict(title="Average Score", side="right", overlaying="y"),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        # Simple analytics without plotly
        st.subheader("Points Distribution")
        top_10 = df_league.head(10)
        st.bar_chart(top_10.set_index('player_name')['total_points'])
        
        st.subheader("Participation vs Performance")
        participation_data = df_players[df_players['total_challenges'] > 0].copy()
        st.scatter_chart(
            participation_data, 
            x='total_challenges', 
            y='total_points',
            size='avg_score'
        )
        
        st.subheader("Weekly Trends")
        weeks = get_available_weeks()
        if len(weeks) > 1:
            trend_data = []
            for week in weeks:
                week_df = get_weekly_standings(week)
                if not week_df.empty:
                    trend_data.append({
                        'week': week,
                        'participants': len(week_df),
                        'avg_score': week_df['score'].mean(),
                        'best_score': week_df['score'].max()
                    })
            
            if trend_data:
                trend_df = pd.DataFrame(trend_data)
                st.line_chart(trend_df.set_index('week')[['participants', 'avg_score']])

if __name__ == "__main__":
    main()
