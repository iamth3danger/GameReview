# Chess Game Review

A comprehensive tool for analyzing chess games.

## Code Structure

The codebase is organized into the following modules:

- **chess_review.py**: Main module with the primary `pgn_game_review` function
- **engine.py**: Handles interaction with the Stockfish chess engine
- **board_analysis.py**: Functions for analyzing chess board states
- **move_analysis.py**: Functions for analyzing individual chess moves
- **game_analysis.py**: Functions for analyzing complete chess games
- **utils.py**: General utility functions
- **piece_utils.py**: Piece-related utilities and constants
- **metrics.py**: Functions for calculating various chess metrics
- **openings.py**: Functions for recognizing chess openings

## Main Function

The main function for analyzing a game is `pgn_game_review()` which takes the following parameters:

- `pgn_data`: The PGN data of the chess game as a string
- `roast`: Boolean indicating whether to provide humorous/sarcastic reviews (default: False)
- `limit_type`: Either "time" or "depth" for engine analysis (default: "time")
- `time_limit`: Time limit in seconds for engine analysis (default: 0.25)
- `depth_limit`: Depth limit for engine analysis (default: 15)

## Class Structure

The code has been reorganized into classes with static methods:

- **Engine**: Handles Stockfish engine integration
- **BoardAnalyzer**: Analyzes board states
- **MoveAnalyzer**: Analyzes individual moves
- **GameAnalyzer**: Analyzes complete games

## Dependencies

- python-chess
- pandas
- numpy
- tqdm
- Stockfish chess engine

## Usage

```python
from chess_review import pgn_game_review

# Example PGN data
pgn_data = """
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
"""

# Analyze the game
(
    san_moves, 
    fens, 
    scores,
    classification_list,
    review_list,
    best_review_list,
    san_best_moves,
    uci_best_moves,
    devs,
    tens,
    mobs,
    conts,
    white_acc,
    black_acc,
    white_elo_est,
    black_elo_est,
    average_cpl_white,
    average_cpl_black
) = pgn_game_review(pgn_data)

# Print move reviews
for move, review in zip(san_moves, review_list):
    print(f"{move}: {review}")
```
