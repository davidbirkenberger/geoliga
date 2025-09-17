#!/usr/bin/env python3
"""
GeoGuessr API Client

A minimal, functional client for retrieving GeoGuessr challenge results.
Uses only 3 essential cookies for authentication.
"""

import requests
import json
from typing import Dict, List, Optional


class GeoGuessrAPI:
    """GeoGuessr API client with minimal cookie requirements."""
    
    def __init__(self, ncfa_cookie: str, session_cookie: str, gg_token: str):
        """
        Initialize the API client with essential cookies.
        
        Args:
            ncfa_cookie: The _ncfa authentication cookie
            session_cookie: The session cookie
            gg_token: The GeoGuessr token
        """
        self.session = self._setup_session(ncfa_cookie, session_cookie, gg_token)
    
    def _setup_session(self, ncfa_cookie: str, session_cookie: str, gg_token: str) -> requests.Session:
        """Set up a requests session with minimal cookies."""
        s = requests.Session()
        
        # Set only the 3 essential cookies
        essential_cookies = {
            '_ncfa': ncfa_cookie,
            'session': session_cookie,
            'gg_token': gg_token
        }
        
        for name, value in essential_cookies.items():
            s.cookies.set(name, value, domain='.geoguessr.com')
        
        # Set headers
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "X-Client": "web",
            "Sec-CH-UA": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": '"Android"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
        })
        
        return s
    
    def get_challenge_results(self, challenge_id: str, friends_only: bool = False, limit: int = 50) -> Optional[Dict]:
        """
        Get challenge results from GeoGuessr API.
        
        Args:
            challenge_id: The challenge ID
            friends_only: Whether to show only friends' results
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing results data or None if failed
        """
        url = f"https://www.geoguessr.com/api/v3/results/highscores/{challenge_id}"
        
        params = {
            'friends': str(friends_only).lower(),
            'limit': limit,
            'minRounds': 5
        }
        
        headers = {
            'Referer': f'https://www.geoguessr.com/de/results/{challenge_id}'
        }
        
        try:
            response = self.session.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    def parse_results(self, results_data: Dict) -> List[Dict]:
        """
        Parse results data to extract player information.
        
        Args:
            results_data: Raw results data from API
            
        Returns:
            List of parsed result dictionaries
        """
        if not results_data or 'items' not in results_data:
            return []
        
        results = []
        items = results_data['items']
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            
            # Extract data from nested structure: item.game.player
            game_info = item.get('game', {})
            player_info = game_info.get('player', {})
            
            # Extract score information
            total_score_info = player_info.get('totalScore', {})
            total_distance_info = player_info.get('totalDistance', {})
            
            result = {
                'rank': i + 1,
                'username': player_info.get('nick', 'Unknown'),
                'userId': player_info.get('id'),
                'totalScore': int(total_score_info.get('amount', 0)) if total_score_info.get('amount') else 0,
                'totalDistance': total_distance_info.get('meters', {}).get('amount', 0) if total_distance_info.get('meters') else 0,
                'totalTime': player_info.get('totalTime', 0),
                'gameId': game_info.get('token'),
                'gameState': game_info.get('state'),
                'roundCount': game_info.get('roundCount', 0),
                'timeLimit': game_info.get('timeLimit', 0),
                'rounds': game_info.get('rounds', []),
                'countryCode': player_info.get('countryCode'),
                'isVerified': player_info.get('isVerified', False),
            }
            
            results.append(result)
        
        return results
    
    def get_challenge_leaderboard(self, challenge_id: str, friends_only: bool = False, limit: int = 50) -> List[Dict]:
        """
        Get challenge leaderboard with parsed results.
        
        Args:
            challenge_id: The challenge ID
            friends_only: Whether to show only friends' results
            limit: Maximum number of results to return
            
        Returns:
            List of parsed leaderboard entries
        """
        results_data = self.get_challenge_results(challenge_id, friends_only, limit)
        if results_data:
            return self.parse_results(results_data)
        return []


def create_client(ncfa_cookie: str, session_cookie: str, gg_token: str) -> GeoGuessrAPI:
    """
    Create a GeoGuessr API client with the provided cookies.
    
    Args:
        ncfa_cookie: The _ncfa authentication cookie
        session_cookie: The session cookie
        gg_token: The GeoGuessr token
        
    Returns:
        Configured GeoGuessrAPI client
    """
    return GeoGuessrAPI(ncfa_cookie, session_cookie, gg_token)


def main():
    """Example usage of the GeoGuessr API client."""
    # Example cookies (replace with your actual cookies)
    ncfa_cookie = "gfX39xMWjNdWcLzkLCfhiqPvnypWmxkTcU6p0P8%2Fyeo%3DbH13%2FmABJMpsvyB05GPf0zN3ocCWQwc6Y1apZo8QzRydns%2FPA82izn%2FIwBoj6mAjZxGyuM6m0yNgInTcsR2AFr1oglI8b%2Fb5mSwHEkLGmHY%3D"
    session_cookie = "eyJTZXNzaW9uSWQiOiJodXZpYmJ2YnhkMjA4c3lxZGliaGJ0amZyaGN1Nm51eiIsIkV4cGlyZXMiOiIyMDI1LTA5LTE3VDE5OjQ0OjM0LjQ4NDQ1ODZaIn0%3D"
    gg_token = "764a038f-2841-4fa5-803f-ec5189e79d4c"
    
    # Create client
    client = create_client(ncfa_cookie, session_cookie, gg_token)
    
    # Get challenge results
    challenge_id = "FbxiQzxzq9XuwwY2"
    results = client.get_challenge_leaderboard(challenge_id, friends_only=False, limit=50)
    
    if results:
        print(f"Found {len(results)} results for challenge {challenge_id}")
        for result in results[:5]:  # Show first 5 results
            time_str = f"{result['totalTime']//60:02d}:{result['totalTime']%60:02d}" if result['totalTime'] else "N/A"
            print(f"{result['rank']}. {result['username']} - {result['totalScore']} points ({result['totalDistance']} km) {time_str}")
    else:
        print("No results found")


if __name__ == "__main__":
    main()