# Historical data
DATA_DIR = 'data'

# Main endpoint
BASE_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'

# Matchups
FIXTURES_ENDPOINT = "https://fantasy.premierleague.com/api/fixtures/"

# Player profiles for each position
DEF = "defensive"
OFF = "offensive"
PLAYER_PROFILE = {
        "Goalkeeper": DEF,
        "Defender": DEF,
        "Midfielder": OFF,
        "Forward": OFF,
}

# Limits in the selected team
LIMITS = {
    "position": {
        "Goalkeeper": 2,
        "Defender": 5,
        "Midfielder": 5,
        "Forward": 3
    },
    "one_team": 3,
    "all": 15
}
