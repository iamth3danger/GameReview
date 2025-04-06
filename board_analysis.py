import chess
from piece_utils import piece_dict

class BoardAnalyzer:
    """Class for analyzing chess board states"""
    
    @staticmethod
    def is_defended(board, square, by_color=None, return_list_of_defenders=False):
        """Check if a piece is defended"""
        piece = board.piece_at(square)
        
        if piece is None:
            if return_list_of_defenders:
                return []
            return False

        if by_color is None:
            defenders = board.attackers(piece.color, square)
        else:
            defenders = board.attackers(by_color, square)

        if return_list_of_defenders:
            return defenders
        
        if len(defenders) > 0:
            return True
        
        return False
    
    @staticmethod
    def is_hanging(board, square, capturable_by=None, return_list_of_attackers=False):
        """Check if a piece is hanging"""
        maybe_hanging_piece = board.piece_at(square)
        
        if maybe_hanging_piece is None:
            if return_list_of_attackers:
                return []
            return False

        if capturable_by is None:
            square_is_defended = BoardAnalyzer.is_defended(board, square)

            if not square_is_defended:
                attackers = list(board.attackers(not maybe_hanging_piece.color, square))
                if len(attackers) > 0:
                    if return_list_of_attackers:
                        return attackers
                    else:
                        return True
                else:
                    return False
        else:
            square_is_defended = BoardAnalyzer.is_defended(board, square, not capturable_by)

            if not square_is_defended:
                attackers = list(board.attackers(capturable_by, square))
            
                if len(attackers) > 0:
                    if return_list_of_attackers:
                        return attackers
                    else:
                        return True
                else:
                    return False
        
            
        return False
    
    @staticmethod
    def check_for_hanging_pieces(board, return_list_of_hanging=False, fr_format=False):
        """Check for hanging pieces on the board"""
        hanging_pieces = []
        hanging_pieces_and_attackers = dict()

        for square in chess.SQUARES:
            maybe_hanging_piece = board.piece_at(square)
            
            if (maybe_hanging_piece is not None):
                if not (BoardAnalyzer.is_defended(board, square)):
                    attackers = list(board.attackers(not maybe_hanging_piece.color, square))
                    if len(attackers) > 0:
                        if fr_format:
                            hanging_pieces_and_attackers[chess.square_name(square)] = [chess.square_name(s) for s in attackers]
                            hanging_pieces.append(chess.square_name(square))
                        else:
                            hanging_pieces_and_attackers[square] = attackers
                            hanging_pieces.append(square)

        if return_list_of_hanging:
            return hanging_pieces
        else:
            return hanging_pieces_and_attackers
    
    @staticmethod
    def is_forking(board, square, return_forked_squares=False):
        """Check if a piece is forking others"""
        if board.piece_at(square) is None:
            if return_forked_squares:
                return []
            return False
            
        forked_squares = []

        square_can_be_captured_by = not board.piece_at(square).color

        if len(board.attackers(square_can_be_captured_by, square)) > 0:
            if (not BoardAnalyzer.is_defended(board, square, not square_can_be_captured_by)):
                if return_forked_squares:
                    return []
                return False

        attacks = board.attacks(square)
        for attacked_square in attacks:
            attacked_piece = board.piece_at(attacked_square)
            if (attacked_piece is not None) and (attacked_piece.color != board.piece_at(square).color):
                if not BoardAnalyzer.is_defended(board, attacked_square):
                    forked_squares.append(attacked_square)
                else:
                    if board.piece_type_at(attacked_square) > board.piece_type_at(square):
                        forked_squares.append(attacked_square)

                    elif board.piece_type_at(attacked_square) < board.piece_type_at(square):
                        if str(attacked_piece).lower() == 'k':
                            forked_squares.append(attacked_square)

        if return_forked_squares:
            return forked_squares
        
        else:   
            if len(forked_squares) >= 2:
                return True
            else:
                return False
    
    @staticmethod
    def is_trapped(board, square, by):
        """Check if a piece is trapped"""
        if board.piece_at(square) is None:
            return False
            
        if str(board.piece_at(square)).lower() == 'k':
            return False

        attackers = board.attackers(by, square)

        capturable_by_lower = False

        for attacking_square in attackers:
            if board.piece_at(attacking_square).color != board.piece_at(square).color:
                if board.piece_type_at(attacking_square) < board.piece_type_at(square):
                    capturable_by_lower = True
        
        if not capturable_by_lower:
            return False

        can_be_saved = True

        movable_squares = board.attacks(square)

        for move_to_square in movable_squares:
            if board.piece_at(move_to_square) is None:
                defending_squares = board.attackers(by, move_to_square)
                
                if len(defending_squares) == 0:
                    can_be_saved = True
                    return False

                for defending_square in defending_squares:
                    if board.piece_at(defending_square).color != board.piece_at(square).color:
                        if board.piece_type_at(defending_square) < board.piece_type_at(square):
                            if not board.is_pinned(by, defending_square):
                                can_be_saved = False   
                            else:
                                can_be_saved = True
            
                        elif board.piece_type_at(defending_square) == board.piece_type_at(square):
                            if not board.is_pinned(by, defending_square):
                                defenders = BoardAnalyzer.is_defended(
                                    board, defending_square, by_color=not by, return_list_of_defenders=True)
                                if len(defenders) <= 1:  # if the trapped piece is the only defender
                                    can_be_saved = False

                        else:
                            can_be_saved = True 

            elif (board.piece_at(move_to_square).color != board.piece_at(square).color) and (board.piece_type_at(move_to_square) <= board.piece_type_at(square)):
                defending_squares = board.attackers(by, move_to_square)
                
                if len(defending_squares) == 0:
                    can_be_saved = True
                    return False

                for defending_square in defending_squares:
                    if board.piece_at(defending_square).color != board.piece_at(square).color:
                        if board.piece_type_at(defending_square) < board.piece_type_at(square):
                            if not board.is_pinned(by, defending_square):
                                can_be_saved = False   
                            else:
                                can_be_saved = True
            
                        elif board.piece_type_at(defending_square) == board.piece_type_at(square):
                            if not board.is_pinned(by, defending_square):
                                defenders = BoardAnalyzer.is_defended(
                                    board, defending_square, by_color=not by, return_list_of_defenders=True)
                                if len(defenders) <= 1:  # if the trapped piece is the only defender
                                    can_be_saved = False

                        else:
                            can_be_saved = True 

        if not can_be_saved:
            return True
        else:
            return False
    
    @staticmethod
    def is_endgame(board):
        """Check if the position is in the endgame phase"""
        major_pieces = 0
        fen = board.fen()
        for p in fen.split(' ')[0]:
            if p.lower() in ['r', 'b', 'n', 'q']:
                major_pieces += 1

        if major_pieces < 6:
            return True
        else:
            return False
            
    @staticmethod
    def is_capturable_by_lower_piece(board, square, capturable_by):
        """Check if a piece can be captured by a lower value piece"""
        if board.piece_at(square) is None:
            return False
            
        attacker_squares = board.attackers(capturable_by, square)

        for attacker_square in attacker_squares:
            if board.piece_type_at(attacker_square) < board.piece_type_at(square):
                return True
        
        return False
    
    @staticmethod
    def check_for_capturable_pieces_by_lower(board):
        """Find all pieces that can be captured by lower value pieces"""
        capturable_squares = []

        for square in board.piece_map():
            if board.piece_at(square).color != board.turn:
                if BoardAnalyzer.is_capturable_by_lower_piece(board, square, capturable_by=board.turn):
                    capturable_squares.append(square)

        return capturable_squares
        
    @staticmethod
    def calculate_material(board):
        """Calculate material balance for both sides"""
        white_material = 0
        black_material = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                if piece.color == True:
                    white_material += piece.piece_type
                else:
                    black_material += piece.piece_type

        return white_material, black_material
    
    @staticmethod
    def get_development(board):
        """Calculate development status for both sides"""
        white_dev = 0
        black_dev = 0

        for square in [chess.A1, chess.H1]:
            if str(board.piece_at(square)) != 'R':
                white_dev += 1

        for square in [chess.B1, chess.G1]:
            if str(board.piece_at(square)) != 'N':
                white_dev += 1

        for square in [chess.C1, chess.F1]:
            if str(board.piece_at(square)) != 'B':
                white_dev += 1

        if board.piece_at(chess.D1) is None or str(board.piece_at(chess.D1)) != 'Q':
            white_dev += 1

        for square in [chess.A8, chess.H8]:
            if str(board.piece_at(square)) != 'r':
                black_dev += 1

        for square in [chess.B8, chess.G8]:
            if str(board.piece_at(square)) != 'n':
                black_dev += 1

        for square in [chess.C8, chess.F8]:
            if str(board.piece_at(square)) != 'b':
                black_dev += 1

        if str(board.piece_at(chess.D8)) != 'q':
            black_dev += 1

        return white_dev, black_dev
    
    @staticmethod
    def get_tension(board):
        """Calculate position tension (number of possible captures) for both sides"""
        player_tension = sum(1 for move in board.legal_moves if board.is_capture(move))
        board.push(chess.Move.null())  # Make a null move to switch turns
        opponent_tension = sum(1 for move in board.legal_moves if board.is_capture(move))
        board.pop()  # Undo the null move

        if board.turn == True:
            return player_tension, opponent_tension
        else:
            return opponent_tension, player_tension
    
    @staticmethod
    def get_mobility(board):
        """Calculate mobility (number of possible non-pawn moves) for both sides"""
        player_mobility = sum(1 for move in board.legal_moves if 
                             board.piece_at(move.from_square) is not None and 
                             str(board.piece_at(move.from_square)).lower() != 'p')
        board.push(chess.Move.null())  # Make a null move to switch turns
        opponent_mobility = sum(1 for move in board.legal_moves if 
                               board.piece_at(move.from_square) is not None and 
                               str(board.piece_at(move.from_square)).lower() != 'p')
        board.pop()  # Undo the null move

        if board.turn == True:
            return player_mobility, opponent_mobility  # white, black
        else:
            return opponent_mobility, player_mobility  # white, black
    
    @staticmethod
    def get_control(board):
        """Calculate board control (number of attacked squares) for both sides"""
        white_control = 0
        black_control = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                if piece.color == True:
                    white_control += len(board.attacks(square))
                else:
                    black_control += len(board.attacks(square))

        return white_control, black_control
