"""Utility functions for chess game analysis"""
import io
import chess
import chess.pgn

def format_item_list(items):
    """Format a list of items into a readable string with commas and 'and'"""
    if len(items) == 0:
        return ""

    if len(items) == 1:
        return items[0]

    formatted_items = ", ".join(items[:-1]) + ", and " + items[-1]
    return formatted_items

def parse_pgn(pgn, san_only=False):
    """Parse a PGN string to extract moves and positions"""
    pgn = io.StringIO(pgn)
    pgn = chess.pgn.read_game(pgn)

    board = chess.Board()

    san_moves = []
    uci_moves = []
    fens = []

    if san_only:
        for move in pgn.mainline_moves():
            san_moves.append(board.san(move))
            board.push(move)
            fens.append(board.fen())

        return san_moves, fens

    else:
        for move in pgn.mainline_moves():
            san_moves.append(board.san(move))
            board.push(move)
            uci_moves.append(move)
            fens.append(board.fen())
    
        return uci_moves, san_moves, fens

def convert_movelist_to_pgn(moves):
    """Convert a list of moves to PGN format"""
    pgn = ""
    move_number = 1

    for move in moves:
        if move_number % 2 == 1:
            pgn += f"{move_number // 2 + 1}.{move} "
        else:
            pgn += f"{move} "

        move_number += 1

    return pgn.strip()

def get_board_pgn(board):
    """Generate PGN from a board position"""
    game = chess.pgn.Game()
    node = game

    # Replay all moves
    for move in board.move_stack:
        node = node.add_variation(move)

    # Return moves in string format
    return str(game.mainline_moves())

def mate_in_n_for(board):
    """Get a description of a checkmate situation"""
    from engine import engine
    import chess.engine
    
    # Get score info
    with chess.engine.SimpleEngine.popen_uci(engine.stockfish_path) as stockfish:
        info = stockfish.analyse(board, chess.engine.Limit(**engine.config))
    score = str(info['score'].relative)

    if '#' not in score:
        return None

    n = int(''.join([i for i in score if i.isdigit()]))

    if '-' in score:
        losing_side = 'Black' if (board.turn == False) else 'White'
        return f'{losing_side} gets checkmated in {n}. '
    elif '+' in score:
        losing_side = 'Black' if (board.turn == True) else 'White'
        return f'{losing_side} gets checkmated in {n}. '
    
    return None
