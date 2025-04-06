"""Module for chess opening recognition"""
import pandas as pd

# Load openings database
try:
    openings_df = pd.read_csv("openings_master.csv")
except Exception as e:
    print(f"Warning: Could not load openings database: {e}")
    # Create an empty DataFrame with the expected columns
    openings_df = pd.DataFrame(columns=["pgn", "name"])

def search_opening(pgn):
    """Search for an opening in the database by PGN string"""
    try:
        # Check if the search_string is in column 'pgn'
        mask = openings_df['pgn'] == pgn

        # If there is a match, return the corresponding value in column 'name'
        if any(mask):
            return openings_df.loc[mask, 'name'].iloc[0]
        else:
            return None
    except Exception as e:
        print(f"Error searching for opening: {e}")
        return None

def is_an_opening(game, return_name_and_desc=True):
    """Check if a game matches a known opening"""
    try:
        opening = openings_df[openings_df['Moves'] == game]
        
        if return_name_and_desc:
            if opening.empty:
                return None, None
            else:
                return (opening['Name'].iloc[0], opening['Description'].iloc[0])
        else:
            return not opening.empty
    except Exception as e:
        print(f"Error checking if game is an opening: {e}")
        if return_name_and_desc:
            return None, None
        else:
            return False
