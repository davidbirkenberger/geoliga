# GeoGuessr League System

A complete weekly GeoGuessr league management system with minimal authentication and automated scoring.

## 🎯 Features

- **Minimal Authentication**: Uses only 3 essential cookies (down from 27!)
- **Weekly League**: Monday-Sunday challenge cycles with rank-based scoring
- **First Attempt Only**: Tracks only the first attempt per player per week
- **SQLite Database**: Persistent storage with automatic standings calculation
- **WhatsApp Ready**: Formatted messages ready to copy and paste
- **Clean API**: Object-oriented design with simple methods

## 🚀 Quick Start

### Installation

```bash
pip install requests
```

### Weekly League Management

```bash
# 1. Create a new weekly challenge (Monday)
python weekly_league.py create FbxiQzxzq9XuwwY2 "A Community World"

# 2. Process results (anytime during the week)
python weekly_league.py process FbxiQzxzq9XuwwY2

# 3. Close the weekly challenge (Sunday)
python weekly_league.py close FbxiQzxzq9XuwwY2

# 4. View standings
python weekly_league.py standings
python weekly_league.py league
```

### Basic API Usage

```python
from geoguessr_api import create_client

# Create client with your cookies
client = create_client(
    ncfa_cookie="your_ncfa_cookie_here",
    session_cookie="your_session_cookie_here", 
    gg_token="your_gg_token_here"
)

# Get challenge results
results = client.get_challenge_leaderboard("FbxiQzxzq9XuwwY2")

# Process results
for result in results:
    print(f"{result['rank']}. {result['username']} - {result['totalScore']} points")
```

### Advanced Usage

```python
from geoguessr_api import GeoGuessrAPI

# Create client directly
client = GeoGuessrAPI(ncfa_cookie, session_cookie, gg_token)

# Get raw API data
raw_data = client.get_challenge_results("challenge_id", friends_only=False, limit=100)

# Parse results manually
parsed_results = client.parse_results(raw_data)

# Get leaderboard
leaderboard = client.get_challenge_leaderboard("challenge_id", limit=50)
```

## 🍪 Getting Your Cookies

### Method 1: Browser Developer Tools
1. Go to GeoGuessr in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage → Cookies
4. Find these 3 cookies:
   - `_ncfa`
   - `session` 
   - `gg_token`

### Method 2: Network Tab
1. Go to a challenge results page
2. Open Network tab in DevTools
3. Find the API call to `/api/v3/results/highscores/`
4. Copy the cookie values from the request headers

## 📊 API Reference

### `GeoGuessrAPI` Class

#### `__init__(ncfa_cookie, session_cookie, gg_token)`
Initialize the API client with essential cookies.

#### `get_challenge_results(challenge_id, friends_only=False, limit=50)`
Get raw challenge results from the API.
- Returns: `Dict` with API response or `None` if failed

#### `parse_results(results_data)`
Parse raw API data into structured results.
- Returns: `List[Dict]` with parsed player data

#### `get_challenge_leaderboard(challenge_id, friends_only=False, limit=50)`
Get parsed challenge leaderboard.
- Returns: `List[Dict]` with leaderboard entries

### Result Data Structure

```python
{
    'rank': 1,
    'username': 'PlayerName',
    'userId': 'user_id',
    'totalScore': 25000,
    'totalDistance': 1000.5,
    'totalTime': 180,
    'gameId': 'game_token',
    'gameState': 'finished',
    'roundCount': 5,
    'timeLimit': 0,
    'rounds': [...],
    'countryCode': 'us',
    'isVerified': False
}
```

## 🔧 Configuration

### Required Cookies

Only 3 cookies are needed:

1. **`_ncfa`** - Main authentication cookie
2. **`session`** - Session management cookie  
3. **`gg_token`** - GeoGuessr-specific token

### Cookie Expiration

- **`_ncfa`**: ~1 year
- **`session`**: ~1 year
- **`gg_token`**: Long-term

Update cookies when you get 401/403 errors.

## 🛠️ Error Handling

```python
client = create_client(ncfa_cookie, session_cookie, gg_token)
results = client.get_challenge_leaderboard("challenge_id")

if not results:
    print("Failed to get results - check cookies or challenge ID")
else:
    print(f"Successfully retrieved {len(results)} results")
```

## 📝 Example Output

```
Found 17 results for challenge FbxiQzxzq9XuwwY2
1. Geosky - 15335 points (15905.3 km) 17:57
2. Chinker - 13464 points (7731.9 km) 1374:39
3. Gat15 - 11739 points (8568.4 km) 04:18
4. TheFlane34 - 9888 points (10440.7 km) 01:55
5. m1r - 9604 points (16345.3 km) 05:18
```

## 🎉 Success!

This client successfully retrieves GeoGuessr challenge results using the official API with minimal authentication requirements.