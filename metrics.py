"""Module for calculating chess game metrics"""
from collections import Counter
import chess

def get_lost_pieces(board):
    """Calculate which pieces have been captured for both sides"""
    default_pieces_white = ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'Q', 'K', 'N', 'N', 'B', 'B', 'R', 'R']
    counter_default_white = Counter(default_pieces_white)
    default_pieces_black = [p.lower() for p in default_pieces_white]
    counter_default_black = Counter(default_pieces_black)

    # Get pieces currently on board
    pieces = [str(p) for p in board.piece_map().values()]

    white_piece_list = [p for p in pieces if p.isupper()]
    black_piece_list = [p for p in pieces if p.islower()]

    counter_white = Counter(white_piece_list)
    counter_black = Counter(black_piece_list)

    lost_white_pieces = list((counter_default_white - counter_white).elements())
    lost_black_pieces = list((counter_default_black - counter_black).elements())
    
    return lost_white_pieces, lost_black_pieces
