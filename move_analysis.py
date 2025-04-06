import chess
from board_analysis import BoardAnalyzer
from engine import engine

class MoveAnalyzer:
    """Class for analyzing individual chess moves"""
    
    @staticmethod
    def move_hangs_piece(board, move, return_hanging_squares=False):
        """Check if a move hangs a piece"""
        position_after_move = board.copy()
        position_after_move.push(move)

        hanging_before = BoardAnalyzer.check_for_hanging_pieces(board, return_list_of_hanging=True)
        hanging_after = BoardAnalyzer.check_for_hanging_pieces(position_after_move, return_list_of_hanging=True)

        if return_hanging_squares:
            return hanging_after
        else:
            if hanging_before == hanging_after:
                return False
            else:
                return True
    
    @staticmethod
    def move_defends_hanging_piece(board, move, return_list_defended=False):
        """Check if a move defends a hanging piece"""
        if board.is_castling(move):
            if return_list_defended:
                return []
            return False
        
        position_after_move = board.copy()
        position_after_move.push(move)

        defended_squares = []
        for defended_square in position_after_move.attacks(move.to_square):
            defended_piece = position_after_move.piece_at(defended_square)
            if (defended_piece is not None) and (defended_piece.color == board.turn):
                if not BoardAnalyzer.is_defended(board, defended_square, by_color=board.turn):
                    defended_squares.append(defended_square)
        
        if return_list_defended:
            return defended_squares

        if len(defended_squares) > 0:
            return True
        else:
            return False
    
    @staticmethod
    def move_creates_fork(board, move, return_forked_squares=False):
        """Check if a move creates a fork"""
        position_after_move = board.copy()
        position_after_move.push(move)

        return BoardAnalyzer.is_forking(position_after_move, move.to_square, return_forked_squares)
    
    @staticmethod
    def move_allows_fork(board, move, return_forking_moves=False):
        """Check if a move allows opponent to create a fork"""
        forking_moves = []

        position_after_move = board.copy()
        position_after_move.push(move)

        for maybe_forking_move in position_after_move.legal_moves:
            if MoveAnalyzer.move_creates_fork(position_after_move, maybe_forking_move):
                forking_moves.append(maybe_forking_move)

        if return_forking_moves:
            return forking_moves
        
        return len(forking_moves) > 0
    
    @staticmethod
    def move_misses_fork(board, move, return_forking_moves=False):
        """Check if a move misses an opportunity to create a fork"""
        forking_moves = []

        for maybe_fork_move in board.legal_moves:
            if MoveAnalyzer.move_creates_fork(board, maybe_fork_move):
                forking_moves.append(maybe_fork_move)

        if return_forking_moves:
            return forking_moves
            
        if move in forking_moves:
            return False
        else:
            return True
    
    @staticmethod
    def move_blocks_check(board, move):
        """Check if a move blocks a check"""
        if (board.is_check()) and (not board.is_capture(move)):
            king_square = board.king(board.turn)   
            position_after_move = board.copy()
            position_after_move.push(move)

            if position_after_move.piece_at(king_square) is not None and str(position_after_move.piece_at(king_square)).lower() == 'k':
                return True
            else:
                return False
            
        else:
            return False
    
    @staticmethod
    def move_allows_mate(board, move, return_winning_player=False):
        """Check if a move allows a checkmate"""
        position_after_move = board.copy()
        position_after_move.push(move)

        result = engine.has_mate_in_n(position_after_move)
        
        if not result:
            if return_winning_player:
                return None
            return False
            
        # Get score info
        with chess.engine.SimpleEngine.popen_uci(engine.stockfish_path) as stockfish:
            info = stockfish.analyse(position_after_move, chess.engine.Limit(**engine.config))
        score = str(info['score'].relative)
        
        if return_winning_player:
            if '+' in score:
                return not board.turn
            elif '-' in score:
                return board.turn
                
        return True
    
    @staticmethod
    def calculate_points_gained_by_move(board, move, **kwargs):
        """Calculate the points gained or lost by a move"""
        previous_score = engine.evaluate(board)

        position_after_move = board.copy()
        position_after_move.push(move)

        current_score, n = engine.evaluate(position_after_move, return_mate_n=True)
        
        if board.turn == True:
            if (previous_score != 10000) and (current_score == 10000):
                return f'mates {n}'
            elif (previous_score == 10000) and (current_score == 10000):
                return f'mates {n}'
            elif (previous_score == -10000) and (current_score == -10000):
                return f'continues gets mated {n}'
            elif (previous_score != -10000) and (current_score == -10000):
                return f'gets mated {n}'
            elif (previous_score == 10000) and (current_score != 10000):
                return f'lost mate'
            
            points_gained = current_score - previous_score
        else:
            if (previous_score != -10000) and (current_score == -10000):
                return f'mates {n}'
            elif (previous_score == -10000) and (current_score == -10000):
                return f'mates {n}'
            elif (previous_score == 10000) and (current_score == 10000):
                return f'continues gets mated {n}'
            elif (previous_score != 10000) and (current_score == 10000):
                return f'gets mated {n}'
            elif (previous_score == -10000) and (current_score != -10000):
                return f'lost mate'

            points_gained = previous_score - current_score

        return points_gained
    
    @staticmethod
    def classify_move(board, move):
        """Classify a move based on its evaluation"""
        points_gained = MoveAnalyzer.calculate_points_gained_by_move(board, move)

        if type(points_gained) == str:
            # Handle string results which are special cases
            if 'mates' in points_gained: 
                return points_gained
            elif 'continues gets mated' in points_gained:
                return points_gained
            elif 'gets mated' in points_gained:
                return points_gained
            elif 'lost mate' in points_gained:
                return points_gained

        # Classify based on centipawn loss
        if (points_gained >= -20):
            return 'excellent'
        elif (points_gained < -20) and (points_gained >= -100):
            return 'good'
        elif (points_gained < -100) and (points_gained >= -250):
            return 'inaccuracy'
        elif (points_gained < -250) and (points_gained >= -450):
            return 'mistake'
        else:
            return 'blunder'
    
    @staticmethod
    def is_developing_move(board, move):
        """Check if a move develops a piece"""
        if board.piece_at(move.from_square) is None:
            return False
            
        if move.from_square in [chess.B1, chess.G1, chess.B8, chess.G8]:
            if str(board.piece_at(move.from_square)).lower() == 'n':
                return 'N'
            else:
                return False
        elif move.from_square in [chess.C1, chess.F1, chess.C8, chess.F8]:
            if str(board.piece_at(move.from_square)).lower() == 'b':
                return 'B'
            else:
                return False
        elif move.from_square in [chess.D1, chess.D8]:  # Fixed from original which had same condition as Bishop twice
            if str(board.piece_at(move.from_square)).lower() == 'q':
                return 'Q'
            else:
                return False
        elif move.from_square in [chess.H1, chess.A1, chess.H8, chess.A8]:
            if str(board.piece_at(move.from_square)).lower() == 'r':
                return 'R'
            else:
                return False
        else:
            return False
    
    @staticmethod
    def is_fianchetto(board, move):
        """Check if a move is a fianchetto (bishop to b2/g2/b7/g7)"""
        if board.piece_at(move.from_square) is None:
            return False
            
        if str(board.piece_at(move.from_square)).lower() == 'b':
            if move.from_square in [chess.C1, chess.F1, chess.C8, chess.F8]:
                if move.to_square in [chess.B2, chess.G2, chess.B7, chess.G7]:
                    return True
            
        return False
    
    @staticmethod
    def is_possible_trade(board, move):
        """Check if a move offers or initiates a trade"""
        if board.piece_at(move.from_square) is None:
            return False
            
        if board.is_capture(move):
            if BoardAnalyzer.is_defended(board, move.to_square, by_color=not board.turn):
                if board.piece_type_at(move.to_square) == board.piece_type_at(move.from_square):
                    return True
                elif (board.piece_type_at(move.to_square) == 2) and (board.piece_type_at(move.from_square) == 3):
                    return True
                elif (board.piece_type_at(move.to_square) == 3) and (board.piece_type_at(move.from_square) == 2):
                    return True
                else:
                    return False
            else:
                return False
        else:
            attackers = list(board.attackers(not board.turn, move.to_square))
            if len(attackers) > 0:
                for attacking_square in attackers:
                    if BoardAnalyzer.is_defended(board, move.to_square, by_color=board.turn):
                        if board.piece_type_at(attacking_square) == board.piece_type_at(move.from_square):
                            if not board.is_pinned(not board.turn, attacking_square):
                                return True
                        elif (board.piece_type_at(attacking_square) == 2) and (board.piece_type_at(move.from_square) == 3):
                            return True
                        elif (board.piece_type_at(attacking_square) == 3) and (board.piece_type_at(move.from_square) == 2):
                            return True
                    else:
                        return True
                
            
            return False
    
    @staticmethod
    def move_is_discovered_check(board, move):
        """Check if a move creates a discovered check"""
        position_after_move = board.copy()
        position_after_move.push(move)

        if position_after_move.is_check():
            for attacked_square in position_after_move.attacks(move.to_square):
                if (position_after_move.piece_at(attacked_square) is not None and 
                    str(position_after_move.piece_at(attacked_square)).lower() == 'k'):
                    return False
            return True
            
        return False
    
    @staticmethod
    def move_is_discovered_check_and_attacks(board, move, return_attacked_squares=False):
        """Check if a move creates a discovered check and attacks another piece"""
        if not MoveAnalyzer.move_is_discovered_check(board, move):
            if return_attacked_squares:
                return []
            return False
        
        position_after_move = board.copy()
        position_after_move.push(move)

        attacked_squares = []

        for attacked_square in position_after_move.attacks(move.to_square):
            if position_after_move.piece_at(attacked_square) is not None:
                if BoardAnalyzer.is_hanging(position_after_move, attacked_square, capturable_by=board.turn):
                    attacked_squares.append(attacked_square)
                elif position_after_move.piece_type_at(attacked_square) > position_after_move.piece_type_at(move.to_square):
                    attacked_squares.append(attacked_square)

        if return_attacked_squares:
            return attacked_squares
        
        return len(attacked_squares) > 0
    
    @staticmethod
    def move_traps_opponents_piece(board, move, return_trapped_squares=False):
        """Check if a move traps an opponent's piece"""
        position_after_move = board.copy()
        position_after_move.push(move)

        trapped_squares = []

        for attacked_square in position_after_move.attacks(move.to_square):
            if position_after_move.piece_at(attacked_square) is not None:
                if position_after_move.piece_at(attacked_square).color != position_after_move.piece_at(move.to_square).color:
                    if BoardAnalyzer.is_trapped(position_after_move, attacked_square, by=board.turn):
                        trapped_squares.append(attacked_square)

        if return_trapped_squares:
            return trapped_squares
        
        return len(trapped_squares) > 0
    
    @staticmethod
    def is_possible_sacrifice(board, move):
        """Check if a move is a potential sacrifice"""
        if board.piece_at(move.from_square) is None:
            return False
            
        if str(board.piece_at(move.from_square)).lower() == 'p':
            return False

        if board.is_capture(move):
            defending_squares = BoardAnalyzer.is_defended(board, move.to_square, by_color=not board.turn, return_list_of_defenders=True)

            if len(defending_squares) > 0:
                if board.piece_type_at(move.to_square) < board.piece_type_at(move.from_square):
                    if (board.piece_type_at(move.to_square) != 2) or (board.piece_type_at(move.from_square) != 3):
                        for defending_square in defending_squares:
                            if board.piece_type_at(defending_square) < board.piece_type_at(move.from_square):
                                return True
                            else:
                                return False
                    else:
                        return False
                else:
                    return False             
            else:
                return False
            
        else:
            attackers = list(board.attackers(not board.turn, move.to_square))
            if len(attackers) > 0:
                for attacking_square in attackers:
                    if BoardAnalyzer.is_defended(board, move.to_square, by_color=board.turn):
                        if board.piece_type_at(attacking_square) < board.piece_type_at(move.from_square):
                            if (board.piece_type_at(attacking_square) != 2) or (board.piece_type_at(move.from_square) != 3):
                                if not board.is_pinned(not board.turn, attacking_square):
                                    return True
                    else:
                        return True
            
            return False
    
    @staticmethod
    def move_pins_opponent(board, move, return_pinned_square=False):
        """Check if a move pins an opponent's piece"""
        if BoardAnalyzer.is_attacked_by(not board.turn, move.to_square):
            if (not BoardAnalyzer.is_defended(board, move.to_square, by_color=board.turn)):
                return False

        position_after_move = board.copy()
        position_after_move.push(move)
        pinned_square = None

        possible_pinned_squares = list(position_after_move.attacks(move.to_square))
        for square in possible_pinned_squares:
            if (position_after_move.piece_at(square) is not None) and (position_after_move.piece_at(square).color == position_after_move.turn):
                if position_after_move.is_pinned(position_after_move.turn, square):
                    pinned_square = square
                    break
                else:
                    pinned_square = None

        if return_pinned_square:
            return pinned_square        

        return pinned_square is not None
    
    @staticmethod
    def board_has_pin(board, return_pin_moves=False):
        """Check if there are pin opportunities on the board"""
        pin_moves = []

        for move in board.legal_moves:
            if MoveAnalyzer.move_pins_opponent(board, move):
                pin_moves.append(move)

        if return_pin_moves:
            return pin_moves
        
        return len(pin_moves) > 0
    
    @staticmethod
    def move_misses_pin(board, move, return_pin_move=False):
        """Check if a move misses an opportunity to pin"""
        pin_moves = MoveAnalyzer.board_has_pin(board, return_pin_moves=True)

        if return_pin_move:
            return pin_moves

        if len(pin_moves) == 0:
            return False
        else:
            if move in pin_moves:
                return False
            else:
                return True
    
    @staticmethod
    def move_misses_mate(board, move):
        """Check if a move misses a mate opportunity"""        
        if engine.has_mate_in_n(board):
            position_after_move = board.copy()
            position_after_move.push(move)
            if engine.has_mate_in_n(position_after_move):
                return False
            else:
                return True
        return False
    
    @staticmethod
    def moves_rook_to_open_file(board, move):
        """Check if a move places a rook on an open file"""
        from_square_reqs = list(range(16)) + list(range(48, 64))
        
        if board.piece_at(move.from_square) is None:
            return False
            
        if str(board.piece_at(move.from_square)).lower() == 'r':
            if move.from_square in from_square_reqs:  # make sure that the rook is coming from 1, 2, 7, or 8th rank
                if abs(move.from_square - move.to_square) < 8:  # make sure that the rook move is horizontal
                    file_name = chess.square_name(move.to_square)[0]
                    num_pieces_on_file = 0
                    for i in range(1, 9):
                        if board.piece_at(chess.parse_square(f'{file_name}{i}')) is not None:
                            num_pieces_on_file += 1

                    if num_pieces_on_file < 3:
                        return True
        
        return False
    
    @staticmethod
    def move_moves_king_off_backrank(board, move):
        """Check if a move takes the king off the back rank (good in endgames)"""
        if board.piece_at(move.from_square) is None:
            return False
            
        backrank_squares = list(range(0, 8)) + list(range(56, 64))
        if BoardAnalyzer.is_endgame(board):
            if str(board.piece_at(move.from_square)).lower() == 'k':
                if move.from_square in backrank_squares:
                    if move.to_square not in backrank_squares:
                        return True
            
        return False
    
    @staticmethod
    def move_attacks_piece(board, move, return_attacked_piece=False):
        """Check if a move attacks an opponent's piece"""
        position_after_move = board.copy()
        position_after_move.push(move)
        
        if (BoardAnalyzer.is_defended(position_after_move, move.to_square) or 
            not board.is_attacked_by(position_after_move.turn, move.to_square)):
            attacked_squares = list(position_after_move.attacks(move.to_square))
            for attacked_square in attacked_squares:
                piece = position_after_move.piece_at(attacked_square)
                if (piece is not None and str(piece).lower() != 'k' and 
                    piece.color != position_after_move.piece_at(move.to_square).color):
                    if (position_after_move.piece_type_at(attacked_square) > 
                        position_after_move.piece_type_at(move.to_square)):
                        if return_attacked_piece:
                            return piece
                        return True
                    elif BoardAnalyzer.is_hanging(position_after_move, attacked_square, 
                                                capturable_by=not position_after_move.turn):
                        if return_attacked_piece:
                            return piece
                        return True
        
        return False
    
    @staticmethod
    def move_wins_tempo(board, move):
        """Check if a move gains a tempo"""
        if not MoveAnalyzer.move_attacks_piece(board, move):
            return False

        points_gained = MoveAnalyzer.calculate_points_gained_by_move(board, move)

        if type(points_gained) == str:
            return False

        return points_gained > 0
    
    @staticmethod
    def move_captures_free_piece(board, move):
        """Check if a move captures an undefended piece"""
        if board.is_capture(move):
            if BoardAnalyzer.is_hanging(board, move.to_square, capturable_by=board.turn):
                return True
            
        return False
    
    @staticmethod
    def move_misses_free_piece(board, move, return_free_captures=False):
        """Check if a move misses capturing a free piece"""
        free_captures = []

        for legal_move in board.legal_moves:
            if MoveAnalyzer.move_captures_free_piece(board, legal_move):
                free_captures.append(legal_move)

        if return_free_captures:
            return free_captures
        
        if len(free_captures) == 0:
            return False
        else:
            if move in free_captures:
                return False
            else:
                return True
    
    @staticmethod
    def move_threatens_mate(board, move):
        """Check if a move creates a mate threat"""
        experiment_board = board.copy()
        experiment_board.push(move)

        if experiment_board.is_check():
            return False

        experiment_board.push(chess.Move.null())

        with chess.engine.SimpleEngine.popen_uci(engine.stockfish_path) as stockfish:
            info = stockfish.analyse(experiment_board, chess.engine.Limit(**engine.config))

        score = str(info['score'].relative)

        return ('#' in score) and ('+' in score)
    
    @staticmethod
    def move_captures_higher_piece(board, move):
        """Check if a move captures a higher value piece"""
        if board.is_capture(move):
            if board.piece_type_at(move.from_square) < board.piece_type_at(move.to_square):
                return True
            
        return False

# Create a global move analyzer instance
move_analyzer = MoveAnalyzer()
