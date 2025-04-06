import math
import numpy as np
from tqdm import tqdm
import chess
from engine import engine
from board_analysis import BoardAnalyzer
from move_analysis import MoveAnalyzer
from utils import format_item_list, parse_pgn, get_board_pgn
from piece_utils import piece_dict
from openings import Opening
class GameAnalyzer:
    """Class for analyzing complete chess games"""
    
    @staticmethod
    def compute_cpl(moves):
        """Calculate centipawn loss (CPL) for a game"""
        cpls_white = []
        cpls_black = []
        scores = []

        board = chess.Board()

        for e, move in enumerate(tqdm(moves)):
            comp_board = board.copy()
            best_move = engine.get_best_move(comp_board)
            comp_board.push(best_move)
            score_best = engine.evaluate(comp_board)
            if score_best == 10000:
                score_best = 1000
            elif score_best == -10000:
                score_best = -1000

            board.push(move)
            score_player = engine.evaluate(board)
            if score_player == 10000:
                score_player = 1000
            elif score_player == -10000:
                score_player = -1000

            scores.append(score_player)

            if e % 2 == 0:
                cpls_white.append(abs(score_best - score_player))
            else:
                cpls_black.append(abs(score_best - score_player))

        average_cpl_white = sum(cpls_white) / len(cpls_white) if cpls_white else 0
        average_cpl_black = sum(cpls_black) / len(cpls_black) if cpls_black else 0

        return scores, cpls_white, cpls_black, average_cpl_white, average_cpl_black
    
    @staticmethod
    def estimate_elo(acpl, n_moves):
        """Estimate player Elo based on average centipawn loss"""
        if acpl > 500:
            return 100
        
        e = 2.71828
        estimate = 3000 * (e ** (-0.01 * acpl)) * ((n_moves / 50) ** 0.5)
        return math.ceil(estimate / 100) * 100
    
    @staticmethod
    def calculate_accuracy(eval_scores):
        """Calculate move accuracy percentages"""
        eval_scores = [0] + eval_scores
        
        def calculate_win_percentage(cp_eval, color):
            if color == 'w':
                return 50 + 50 * (2 / (1 + np.exp(-0.00368208 * cp_eval)) - 1)
            elif color == 'b':
                return 50 + 50 * (2 / (1 + np.exp(0.00368208 * cp_eval)) - 1)
            
        white_win_percentages = [calculate_win_percentage(s, 'w') for s in eval_scores]
        black_win_percentages = [100 - p for p in white_win_percentages]

        # Accuracy% = 103.1668 * exp(-0.04354 * (winPercentBefore - winPercentAfter)) - 3.1669
        white_accuracies = []
        black_accuracies = []
        for i in range(len(white_win_percentages) - 1):
            #100.03072339664806 * exp(-0.10082980372791278 * x) + -0.030767264030683358
            if i % 2 == 0:
                win_delta = white_win_percentages[i] - white_win_percentages[i + 1]
                if win_delta <= 0:
                    white_accuracies.append(100)
                else:
                    accuracy = 100.0307234 * np.exp(-0.1008298 * win_delta) - 0.03076726
                    white_accuracies.append(accuracy)
            else:
                win_delta = black_win_percentages[i] - black_win_percentages[i + 1]
                if win_delta <= 0:
                    black_accuracies.append(100)
                else:
                    accuracy = 100.0307234 * np.exp(-0.1008298 * win_delta) - 0.03076726
                    black_accuracies.append(accuracy)

        return np.mean(white_accuracies), np.mean(black_accuracies)
    
    @staticmethod
    def calculate_metrics(fens):
        """Calculate various metrics for each position in a game"""
        devs = []
        mobs = []
        tens = []
        conts = []

        for fen in fens:
            board = chess.Board(fen)
            devs.append(list(BoardAnalyzer.get_development(board)))
            mobs.append(list(BoardAnalyzer.get_mobility(board)))
            tens.append(list(BoardAnalyzer.get_tension(board)))
            conts.append(list(BoardAnalyzer.get_control(board)))

        return devs, mobs, tens, conts
    
    @staticmethod
    def review_move(board, move, previous_review="", check_if_opening=False):
        """Generate a detailed review of a chess move"""
        position_after_move = board.copy()
        position_after_move.push(move)
        
        review = ''
        best_move = engine.get_best_move(board)

        if check_if_opening:
            
            opening = Opening().search_opening(get_board_pgn(position_after_move))
            if opening is not None:
                review = f'This is a book move. The opening is called {opening}. '
                return 'book', review, best_move, board.san(best_move)
        
        move_classification = MoveAnalyzer.classify_move(board, move)

        if move_classification in ['excellent', 'good']:
            if move == best_move:
                move_classification = "best"
                
            review += f'{board.san(move)} is {move_classification}. '
            
            trade = False

            if MoveAnalyzer.is_possible_trade(board, move) and not MoveAnalyzer.move_is_discovered_check(board, move):
                if board.is_capture(move):
                    review += 'This is a trade. '
                else:
                    review += 'This offers a trade. '
                trade = True

            defended_pieces = MoveAnalyzer.move_defends_hanging_piece(board, move, return_list_defended=True)
            defended_squares = [chess.square_name(s) for s in defended_pieces]
            defended_pieces = [piece_dict[str(board.piece_at(s)).lower()] for s in defended_pieces]

            if 'King' in defended_pieces:
                ki = defended_pieces.index('King')
                del defended_pieces[ki]
                del defended_squares[ki]

            if (len(defended_pieces) > 0) and (trade == False):
                review += f'This defends a {format_item_list(defended_pieces)} on {format_item_list(defended_squares)}. '

            possible_forked_squares = MoveAnalyzer.move_creates_fork(board, move, return_forked_squares=True)
            if len(possible_forked_squares) >= 2:
                forked_pieces = [piece_dict[str(board.piece_at(s)).lower()] for s in possible_forked_squares]
                review += f'This creates a fork on {format_item_list(forked_pieces)}. '
            else:
                possible_attacked_piece = MoveAnalyzer.move_attacks_piece(board, move, return_attacked_piece=True)
                if possible_attacked_piece is not False:
                    review += f'This attacks the {piece_dict[str(possible_attacked_piece).lower()]}. '

            if MoveAnalyzer.move_blocks_check(board, move):
                review += f'This blocks a check to the king with a piece. '

            developing = MoveAnalyzer.is_developing_move(board, move)
            if developing is not False:
                review += f'This develops a {piece_dict[developing.lower()]}. '
            
            if MoveAnalyzer.is_fianchetto(board, move):
                review += 'This fianchettos the bishop by putting it on a powerful diagonal. '

            if MoveAnalyzer.move_pins_opponent(board, move):
                review += 'This pins a piece of the opponent to their king. '

            if MoveAnalyzer.moves_rook_to_open_file(board, move):
                review += "By placing the rook on an open file, it controls important columns. "

            if BoardAnalyzer.is_endgame(board):
                if MoveAnalyzer.move_moves_king_off_backrank(board, move):
                    review += "By moving the king off the back rank, the risk of back rank mate threats is reduced and improve the king's safety. "

            if MoveAnalyzer.move_wins_tempo(board, move):
                review += 'This move gains a tempo. '

            if 'trade' not in previous_review:
                if MoveAnalyzer.move_captures_higher_piece(board, move):
                    review += f'This captures a higher value piece. '

                if 'higher value piece' not in previous_review:
                    if MoveAnalyzer.move_captures_free_piece(board, move):
                        review += f'This captures a free {piece_dict[str(board.piece_at(move.to_square)).lower()]}. '

            attacked_squares_with_check = MoveAnalyzer.move_is_discovered_check_and_attacks(board, move, return_attacked_squares=True)
            if len(attacked_squares_with_check) > 0:
                attacked_pieces_with_check = [board.piece_at(s) for s in attacked_squares_with_check]
                attacked_pieces_with_check = [piece_dict[str(p).lower()] for p in attacked_pieces_with_check]
                review += f'This creates a discovered check whilst attacking a {format_item_list(attacked_pieces_with_check)}. '

            trapped_squares = MoveAnalyzer.move_traps_opponents_piece(board, move, return_trapped_squares=True)
            if len(trapped_squares) > 0:
                trapped_pieces = [board.piece_at(s) for s in trapped_squares]
                trapped_pieces = [piece_dict[str(p).lower()] for p in trapped_pieces]
                review += f'This traps a {format_item_list(trapped_pieces)}. '

            if MoveAnalyzer.is_possible_sacrifice(board, move):
                move_classification = 'brilliant'
                review = review.replace('best', 'brilliant')
                review = review.replace('good', 'brilliant')
                review = review.replace('excellent', 'brilliant')
                review += f'This sacrifices the {piece_dict[str(board.piece_at(move.from_square)).lower()]}. '

            if MoveAnalyzer.move_threatens_mate(board, move):
                review += 'This creates a checkmate threat. '

        # Handle errors, inaccuracies, and blunders
        elif move_classification in ['inaccuracy', 'mistake', 'blunder']:
            # ... (similar to the code in the original function)
            review += f'{board.san(move)} is {move_classification}. '

            possible_hanging_squares = []
            if ('creates a fork' not in previous_review) or (not board.is_check()) or ('trade' not in previous_review) or ('lower value' not in previous_review):
                possible_hanging_squares = MoveAnalyzer.move_hangs_piece(board, move, return_hanging_squares=True)

                if MoveAnalyzer.is_possible_trade(board, move):
                    if move.to_square in possible_hanging_squares:
                        possible_hanging_squares.remove(move.to_square)

                possible_hanging_squares = [s for s in possible_hanging_squares if position_after_move.piece_at(s) and position_after_move.piece_at(s).color == board.turn]
                if len(possible_hanging_squares) > 0:
                    hanging_squares = [chess.square_name(s) for s in possible_hanging_squares]
                    hanging_pieces = [piece_dict[str(position_after_move.piece_at(s)).lower()] for s in possible_hanging_squares]
                    review += f'This move leaves {format_item_list(hanging_pieces)} hanging on {format_item_list(hanging_squares)}. '

            capturable_pieces_by_lower = BoardAnalyzer.check_for_capturable_pieces_by_lower(position_after_move)
            capturable_pieces_by_lower = [s for s in capturable_pieces_by_lower if s not in possible_hanging_squares]

            if (len(capturable_pieces_by_lower) > 0) and (not position_after_move.is_check()) and (not MoveAnalyzer.is_possible_trade(board, move)):
                capturable_pieces_by_lower = [piece_dict[str(position_after_move.piece_at(s)).lower()] for s in capturable_pieces_by_lower]
                review += f'A {format_item_list(capturable_pieces_by_lower)} can be captured by a lower value piece. '

            possible_forking_moves = MoveAnalyzer.move_allows_fork(board, move, return_forking_moves=True)
            
            if engine.get_best_move(position_after_move) in possible_forking_moves:
                review += 'This move leaves pieces vulnerable to a fork. '

            missed_forks = MoveAnalyzer.move_misses_fork(board, move, return_forking_moves=True)
            if (best_move in missed_forks) and (move != best_move):
                review += f'There was a missed fork with {board.san(best_move)}. '

            missed_pins = MoveAnalyzer.move_misses_pin(board, move, return_pin_move=True)
            if (best_move in missed_pins) and (move != best_move):
                review += f"There was a missed pin in the previous move with {board.san(best_move)}. "

            missed_free_captures = MoveAnalyzer.move_misses_free_piece(board, move, return_free_captures=True)
            if len(missed_free_captures) > 0:
                if (best_move in missed_free_captures) and (move != best_move):
                    review += f"An opportunity to take a {piece_dict[str(board.piece_at(best_move.to_square)).lower()]} was lost. "

            lets_opponent_play_move = engine.get_best_move(position_after_move)

            if MoveAnalyzer.move_threatens_mate(board, best_move):
                review += 'This misses an opportunity to create a checkmate threat. '

            missed_attacked_piece = MoveAnalyzer.move_attacks_piece(board, best_move, return_attacked_piece=True)
            if missed_attacked_piece is not False:
                review += f'A chance to attack a {piece_dict[str(missed_attacked_piece).lower()]} with {board.san(best_move)} was missed. '

            if MoveAnalyzer.move_attacks_piece(position_after_move, lets_opponent_play_move):
                review += f'This permits the opponent to attack a piece. '

            review += f"The opponent can play {position_after_move.san(lets_opponent_play_move)}. "

        # Process special mate-related classifications
        elif 'continues gets mated' in move_classification:
            losing_side = 'White' if board.turn else 'Black'
            review += f"{board.san(move)} is good, but {losing_side} will still get checkmated. {losing_side} gets mated in {move_classification[-1]}."
            if move == best_move:
                move_classification = "best"
            else:
                move_classification = 'good'

        elif 'gets mated' in move_classification:
            lets_opponent_play_move = engine.get_best_move(position_after_move)

            losing_side = 'White' if board.turn else 'Black'
            review += f'The opponent can play {position_after_move.san(lets_opponent_play_move)}. '
            review += f"{board.san(move)} is a blunder and allows checkmate. {losing_side} gets mated in {move_classification[-1]}."

            move_classification = 'blunder'
        
        elif 'lost mate' in move_classification:
            lets_opponent_play_move = engine.get_best_move(position_after_move)
            review += f"This loses the checkmate sequence. The opponent can play {position_after_move.san(lets_opponent_play_move)}. "
            move_classification = 'blunder'

        elif 'mates' in move_classification:
            n = 0
            if len(previous_review) > 2:
                n_char = previous_review[-2]  # ex. "White gets mated in 6." we need the number 6
                if n_char.isdigit():  # means that player is continuing checkmate sequence
                    n = int(n_char)

            if n > 0:  # Continue existing mate sequence
                if int(move_classification[-1]) <= n:  # means player is one move less away from mating
                    winning_side = 'White' if board.turn else 'Black'
                    if int(move_classification[-1]) == 0:
                        review += f"Checkmate!"
                    else:
                        review += f"{board.san(move)} continues the checkmate sequence. {winning_side} mates in {move_classification[-1]}."
                
                else:
                    winning_side = 'White' if board.turn else 'Black'
                    review += f"{board.san(move)} is good, but there was a faster way to checkmate. {winning_side} mates in {move_classification[-1]}."
                    move_classification = 'good'

                if move == best_move:
                    move_classification = "best"
            else:
                # Starting a new mate sequence
                winning_side = 'White' if board.turn else 'Black'
                if int(move_classification[-1]) == 0:
                    review += f"Checkmate!"
                else:
                    review += f"{board.san(move)} starts a checkmate sequence. {winning_side} mates in {move_classification[-1]}."
                
                if move == best_move:
                    move_classification = "best"

        return move_classification, review, best_move, board.san(best_move)
    
    @staticmethod
    def review_game(uci_moves, roast=False, verbose=False):
        """Generate a detailed review of a chess game"""
        board = chess.Board()

        san_best_moves = []
        uci_best_moves = []

        classification_list = []

        review_list = []
        best_review_list = []

        for i, move in enumerate(tqdm(uci_moves)):
            check_if_opening = i < 11  # Check for opening in first 11 moves

            if len(review_list) == 0:
                previous_review = ""
            else:
                previous_review = review_list[-1]

            # Either use normal review or roast function based on parameter
            if roast:
                classification, review, uci_best_move, san_best_move = GameAnalyzer.roast_move(
                    board, move, previous_review, check_if_opening)
            else:
                classification, review, uci_best_move, san_best_move = GameAnalyzer.review_move(
                    board, move, previous_review, check_if_opening)
                    
            if classification not in ['book', 'best']:
                _, best_review, _, _ = GameAnalyzer.review_move(board, uci_best_move, previous_review, check_if_opening)
            else:
                best_review = ''

            classification_list.append(classification)
            review_list.append(review)
            best_review_list.append(best_review)
            uci_best_moves.append(uci_best_move)
            san_best_moves.append(san_best_move)
            
            if verbose:
                print(move, end='')
                print(' | ', end='')
                print(review)
                print('')
                print(uci_best_move, end='')
                print(' | ', end='')
                print(best_review)
                print('')
                
            board.push(move)

        return review_list, best_review_list, classification_list, uci_best_moves, san_best_moves
    
    def roast_move(board: chess.Board, move, previous_review: str, check_if_opening=False):
        def format_item_list(items):
            if len(items) == 0:
                return ""

            if len(items) == 1:
                return items[0]

            formatted_items = ", ".join(items[:-1]) + ", and " + items[-1]
            return formatted_items

        position_after_move = board.copy()
        position_after_move.push(move)
        
        review = ''

        best_move = MoveAnalyzer.get_best_move(board)

        if check_if_opening:
            opening = Opening().search_opening(get_board_pgn(position_after_move))
            if opening is not None:
                review = f'This is a book move. The opening is called {opening}. '
                return 'book', review, best_move, board.san(best_move)
        
        move_classication = MoveAnalyzer.classify_move(board, move)

        if move_classication in ['excellent', 'good']:

            if move == best_move:
                move_classication = "best"
                
            review += f'{board.san(move)} is {move_classication}. '
            
            trade = False

            if MoveAnalyzer.is_possible_trade(board, move) and not MoveAnalyzer.move_is_discovered_check(board, move):
                if board.is_capture(move):
                    review += 'This is a trade. '
                else:
                    review += 'This offers a trade. '
                trade = True

            defended_pieces = MoveAnalyzer.move_defends_hanging_piece(board, move, return_list_defended=True)
            defended_squares = [chess.square_name(s) for s in defended_pieces]
            defended_pieces = [piece_dict[str(board.piece_at(s)).lower()] for s in defended_pieces]

            if 'King' in defended_pieces:
                ki = defended_pieces.index('King')
                del defended_pieces[ki]
                del defended_squares[ki]

            if (len(defended_pieces) > 0) and (trade == False):
                
                review += f'This defends a {format_item_list(defended_pieces)} on {format_item_list(defended_squares)}. '

            possible_forked_squares = MoveAnalyzer.move_creates_fork(board, move, return_forked_squares=True)
            if len(possible_forked_squares) >= 2:
                forked_pieces = [piece_dict[str(board.piece_at(s)).lower()] for s in possible_forked_squares]
                review += f'This creates a fork on {format_item_list(forked_pieces)}. '
            else:
                possible_attakced_piece = MoveAnalyzer.move_attacks_piece(board, move, return_attacked_piece=True)
                if possible_attakced_piece is not False:
                    review += f'This attacks the {piece_dict[str(possible_attakced_piece).lower()]}. '


            if MoveAnalyzer.move_blocks_check(board, move):
                review += f'This blocks a check to the king with a piece. '

            developing =  MoveAnalyzer.is_developing_move(board, move)
            if developing is not False:
                review += f'This develops a {piece_dict[developing.lower()]}. '
            
            if MoveAnalyzer.is_fianchetto(board, move):
                review += 'This fianchettos the bishop by putting it on a powerful diagonal. '

            if MoveAnalyzer.move_pins_opponent(board, move):
                review += 'This pins a piece of the opponent to their king. '

            if MoveAnalyzer.moves_rook_to_open_file(board, move):
                review += "By placing the rook on an open file, it controls important columns. "

            if BoardAnalyzer.is_endgame(board):
                if MoveAnalyzer.move_moves_king_off_backrank(board, move):
                    review += "By moving the king off the back rank, the risk of back rank mate threats is reduced and improve the king's safety. "

            if MoveAnalyzer.move_wins_tempo(board, move):
                review += 'This move gains a tempo. '

            if 'trade' not in previous_review:

                if MoveAnalyzer.move_captures_higher_piece(board, move):
                    review += f'This captures a higher value piece. '

                if 'higher value piece' not in previous_review:
                    if MoveAnalyzer.move_captures_free_piece(board, move):
                        review += f'This captures a free {piece_dict[str(board.piece_at(move.to_square)).lower()]}. '

            attacked_squares_with_check = MoveAnalyzer.move_is_discovered_check_and_attacks(board, move, return_attacked_squares=True)
            if len(attacked_squares_with_check) > 0:
                attacked_pieces_with_check = [board.piece_at(s) for s in attacked_squares_with_check]
                attacked_pieces_with_check = [piece_dict[str(p).lower()] for p in attacked_pieces_with_check]
                review += f'This creates a discovered check whilst attacking a {format_item_list(attacked_pieces_with_check)}. '

            trapped_squares = MoveAnalyzer.move_traps_opponents_piece(board, move, return_trapped_squares=True)
            if len(trapped_squares) > 0:
                trapped_pieces = [board.piece_at(s) for s in trapped_squares]
                trapped_pieces = [piece_dict[str(p).lower()] for p in trapped_pieces]
                review += f'This traps a {format_item_list(trapped_pieces)}. '

            if MoveAnalyzer.is_possible_sacrifice(board, move):
                #if move_classication != 'good':
                move_classication = 'brilliant'
                review = review.replace('best', 'brilliant')
                review = review.replace('good', 'brilliant')
                review = review.replace('excellent', 'brilliant')
                review += f'This sacrifices the {piece_dict[str(board.piece_at(move.from_square)).lower()]}. '

            if MoveAnalyzer.move_threatens_mate(board, move):
                review += 'This creates a checkmate threat. '


        elif move_classication in ['inaccuracy', 'mistake', 'blunder']:

            review += f'{board.san(move)} is {move_classication}. '

            possible_hanging_squares = []
            if ('creates a fork' not in previous_review) or (not board.is_check()) or ('trade' not in previous_review) or ('lower value' not in previous_review):
                possible_hanging_squares = MoveAnalyzer.move_hangs_piece(board, move, return_hanging_squares=True)

                if  MoveAnalyzer.is_possible_trade(board, move):
                    if move.to_square in possible_hanging_squares:
                        del possible_hanging_squares[possible_hanging_squares.index(move.to_square)]

                possible_hanging_squares = [s for s in possible_hanging_squares if position_after_move.piece_at(s).color == board.turn]
                if len(possible_hanging_squares) > 0:
                    hanging_squares = [chess.square_name(s) for s in possible_hanging_squares]
                    hanging_pieces = [piece_dict[str(position_after_move.piece_at(s)).lower()] for s in possible_hanging_squares]
                    review += f'This IS SO STUPID. {format_item_list(hanging_pieces)} is fucking hanging on {format_item_list(hanging_squares)}. '

            capturable_pieces_by_lower =  BoardAnalyzer.check_for_capturable_pieces_by_lower(position_after_move)
            capturable_pieces_by_lower = [s for s in capturable_pieces_by_lower if s not in possible_hanging_squares]

            if (len(capturable_pieces_by_lower) > 0) and (not position_after_move.is_check()) and (not MoveAnalyzer.is_possible_trade(board, move)):
                capturable_pieces_by_lower = [piece_dict[str(position_after_move.piece_at(s)).lower()] for s in capturable_pieces_by_lower]
                review += f'A lower value is piece just STARING at {format_item_list(capturable_pieces_by_lower)}. How the fuck can you let that happen? '

            possible_forking_moves = MoveAnalyzer.move_allows_fork(board, move, return_forking_moves=True)
            
            if MoveAnalyzer.get_best_move(position_after_move) in possible_forking_moves:
                review += 'Forky forky forky YOU CAN GET FORKED YOU DUMBASS! '

            missed_forks = MoveAnalyzer.move_misses_fork(board, move, return_forking_moves=True)
            if (best_move in missed_forks) and (move != best_move):
                review += f'Are you blind? You could have forked with {board.san(best_move)}. Smh. '

            missed_pins = MoveAnalyzer.move_misses_pin(board, move, return_pin_move=True)
            if (best_move in missed_pins) and (move != best_move):
                review += f"Just another missed pin with {board.san(best_move)} because of stupidity. "

            missed_free_captures = MoveAnalyzer.move_misses_free_piece(board, move, return_free_captures=True)
            if len(missed_free_captures) > 0:
                if (best_move in missed_free_captures) and (move != best_move):
                    review += f"Can this get any more annoying? You could have taken a {piece_dict[str(board.piece_at(best_move.to_square)).lower()]}. "

            lets_opponent_play_move = MoveAnalyzer.get_best_move(position_after_move)

            if MoveAnalyzer.move_threatens_mate(board, best_move):
                review += "Is this person trying to lose? They could've threatened a fucking forced checkmate. "

            missed_attacked_piece = MoveAnalyzer.move_attacks_piece(board, best_move, return_attacked_piece=True)
            if missed_attacked_piece is not False:
                review += f'This missed attacking {piece_dict[str(missed_attacked_piece).lower()]} with {board.san(best_move)} because they were too pussy. '

            if MoveAnalyzer.move_attacks_piece(position_after_move, lets_opponent_play_move):
                review += f"You're just asking the opponent to attack one of your pieces. "

            attacked_squares_with_check = MoveAnalyzer.move_is_discovered_check_and_attacks(position_after_move, lets_opponent_play_move, return_attacked_squares=True)
            if len(attacked_squares_with_check) > 0:
                attacked_pieces_with_check = [position_after_move.piece_at(s) for s in attacked_squares_with_check]
                attacked_pieces_with_check = [piece_dict[str(p).lower()] for p in attacked_pieces_with_check]
                review += f'This dumbass looses a {format_item_list(attacked_pieces_with_check)} from a discovered check. '

            missed_attacked_squares_with_check = MoveAnalyzer.move_is_discovered_check_and_attacks(board, best_move, return_attacked_squares=True)
            if len(missed_attacked_squares_with_check) > 0:
                missed_attacked_pieces_with_check = [board.piece_at(s) for s in missed_attacked_squares_with_check]
                missed_attacked_pieces_with_check = [piece_dict[str(p).lower()] for p in missed_attacked_pieces_with_check]
                review += f'Understandable that a moron would lose a chance to attack a {format_item_list(missed_attacked_pieces_with_check)} from a discovered check. '

            if not (len(attacked_squares_with_check) > 0):
                trapped_squares = MoveAnalyzer.move_traps_opponents_piece(position_after_move, lets_opponent_play_move, return_trapped_squares=True)
                if len(trapped_squares) > 0:
                    trapped_pieces = [position_after_move.piece_at(s) for s in trapped_squares]
                    trapped_pieces = [piece_dict[str(p).lower()] for p in trapped_pieces]
                    review += f"That's so hilarious! A {format_item_list(trapped_pieces)} can get trapped. "

            missed_trapped_squares = MoveAnalyzer.move_traps_opponents_piece(board, best_move, return_trapped_squares=True)
            if len(missed_trapped_squares) > 0:
                missed_trapped_pieces = [board.piece_at(s) for s in missed_trapped_squares]
                missed_trapped_pieces = [piece_dict[str(p).lower()] for p in missed_trapped_pieces]
                review += f"Why did you let a {format_item_list(missed_trapped_pieces)} escape?? You could've trapped them you dumb fuck. "

            if MoveAnalyzer.move_wins_tempo(position_after_move, lets_opponent_play_move):
                review += f'Sigh. You just let the opponent win a tempo. '

            review += f"The opponent can play {position_after_move.san(lets_opponent_play_move)}. "

        elif 'continues gets mated' in move_classication:
            losing_side = 'White' if board.turn else 'Black'
            review += f"{board.san(move)} is good, but {losing_side} will still get checkmated. {losing_side} gets mated in {move_classication[-1]}."
            if move == best_move:
                move_classication = "best"
            else:
                move_classication = 'good'

        elif 'gets mated' in move_classication:
            lets_opponent_play_move = MoveAnalyzer.get_best_move(position_after_move)

            losing_side = 'White' if board.turn else 'Black'
            review += f'The opponent can play {position_after_move.san(lets_opponent_play_move)}. '
            review += f"{board.san(move)} is a blunder. You tryna sacrifice the game? {losing_side} gets mated in {move_classication[-1]}."

            move_classication = 'blunder'
        
        elif 'lost mate' in move_classication:
            lets_opponent_play_move = MoveAnalyzer.get_best_move(position_after_move)
            review += f"You were winning! Why did you do that? I guess that's expected for a someone with a small brain to lose a checkmate sequence. The opponent can play {position_after_move.san(lets_opponent_play_move)}. "
            move_classication = 'blunder'

        elif 'mates' in move_classication:
            n = previous_review[-2] # ex. "White gets mated in 6." we need the number 6
            if n.isdigit(): # means that player is continuing checkmate sequence

                if int(move_classication[-1]) <= int(n): # means player is one move less away from mating
                    winning_side = 'White' if board.turn else 'Black'
                    if int(move_classication[-1]) == 0:
                        review += f"Checkmate!"
                    else:
                        review += f"{board.san(move)} continues the checkmate sequence. {winning_side} gets mated in {move_classication[-1]}."
                
                else:
                    winning_side = 'White' if board.turn else 'Black'
                    review += f"{board.san(move)} is good, but there was a faster way to checkmate. {winning_side} gets mated in {move_classication[-1]}."
                    move_classication = 'good'

                if move == best_move:
                    move_classication = "best"

    
        return move_classication, review, best_move, board.san(best_move)
    
    @staticmethod
    def seperate_squares_in_move_list(uci_moves):
        """Convert UCI move format to separate from/to square pairs"""
        seperated_squares = []

        for move in uci_moves:
            move = str(move)
            seperated_squares.append([move[:2], move[2:]])

        return seperated_squares
    
    @staticmethod
    def pgn_game_review(pgn_data, roast=False, limit_type="time", time_limit=0.25, depth_limit=15):
        """Complete PGN game analysis"""
        # Configure engine
        engine.set_config(limit_type, time_limit, depth_limit)
        
        # Parse PGN
        uci_moves, san_moves, fens = parse_pgn(pgn_data)
        
        # Calculate metrics
        scores, cpls_white, cpls_black, average_cpl_white, average_cpl_black = GameAnalyzer.compute_cpl(uci_moves)
        n_moves = len(scores) // 2
        
        white_elo_est = GameAnalyzer.estimate_elo(average_cpl_white, n_moves)
        black_elo_est = GameAnalyzer.estimate_elo(average_cpl_black, n_moves)
        
        white_acc, black_acc = GameAnalyzer.calculate_accuracy(scores)
        
        devs, mobs, tens, conts = GameAnalyzer.calculate_metrics(fens)

        # Generate reviews
        review_list, best_review_list, classification_list, uci_best_moves, san_best_moves = GameAnalyzer.review_game(
            uci_moves, roast)

        uci_best_moves = GameAnalyzer.seperate_squares_in_move_list(uci_best_moves)

        return (
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
        )

# Create a global game analyzer instance
game_analyzer = GameAnalyzer()
