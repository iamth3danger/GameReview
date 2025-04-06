"""Main module for chess game review functionality"""
from functools import lru_cache

# Import all components
from engine import engine
from game_analyzer import game_analyzer

@lru_cache(maxsize=128)
def pgn_game_review(pgn_data, roast=False, limit_type="time", time_limit=0.25, depth_limit=15):
    """
    Analyze a chess game from PGN data.
    
    Args:
        pgn_data: String containing the PGN game data
        roast: If True, generate humorous/sarcastic reviews
        limit_type: "time" or "depth" for engine analysis
        time_limit: Time limit in seconds for engine analysis if limit_type is "time"
        depth_limit: Depth limit for engine analysis if limit_type is "depth"
    
    Returns:
        Tuple containing analysis results:
        - san_moves: List of moves in SAN format
        - fens: List of FEN positions after each move
        - scores: List of evaluation scores
        - classification_list: List of move classifications (best, good, inaccuracy, etc.)
        - review_list: List of move reviews
        - best_review_list: List of reviews for best moves
        - san_best_moves: List of best moves in SAN format
        - uci_best_moves: List of best moves in UCI format (as [from, to] pairs)
        - devs: Development metrics list
        - tens: Tension metrics list
        - mobs: Mobility metrics list
        - conts: Control metrics list
        - white_acc: White's move accuracy percentage
        - black_acc: Black's move accuracy percentage
        - white_elo_est: Estimated Elo for White
        - black_elo_est: Estimated Elo for Black
        - average_cpl_white: Average centipawn loss for White
        - average_cpl_black: Average centipawn loss for Black
    """
    return game_analyzer.pgn_game_review(
        pgn_data=pgn_data,
        roast=roast,
        limit_type=limit_type,
        time_limit=time_limit,
        depth_limit=depth_limit
    )
