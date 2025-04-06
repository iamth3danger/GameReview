import chess.engine
import platform

# Configure stockfish path based on platform
stockfish_path = "stockfish"
if "windows" in platform.system().lower():
    stockfish_path += ".exe"

class Engine:
    """Class to handle interactions with the Stockfish engine"""
    
    def __init__(self):
        self.config = {"time": 0.25}
    
    def set_config(self, limit_type, time_limit=None, depth_limit=None):
        """Set engine configuration"""
        if limit_type == "time":
            self.config = {'time': float(time_limit)}
        else:
            self.config = {'depth': int(depth_limit)}
    
    def evaluate(self, board, return_mate_n=False):
        """Evaluate a position using Stockfish"""
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(**self.config))

        possible_mate_score = str(info['score'].relative)
        if '#' in possible_mate_score:
            n = abs(int(possible_mate_score.replace("#", '')))

            if '+' in possible_mate_score:
                if board.turn == True:  # if black played the mate move
                    if return_mate_n:
                        return 10000, n
                    else:
                        return 10000
                else:  # if white played the mate move
                    if return_mate_n:
                        return -10000, n
                    else:
                        return -10000
            else:
                if board.turn == True:  # if black played the mate move
                    if return_mate_n:
                        return -10000, n
                    else:
                        return -10000
                else:  # if white played the mate move
                    if return_mate_n:
                        return 10000, n
                    else:
                        return 10000

        # handle error if score is none when mate in n
        if board.turn == True:
            score = info['score'].relative.score()
        elif board.turn == False:
            score = -info['score'].relative.score()  # transform score to absolute score (pos in favor of white, neg in favor black)

        if return_mate_n:
            return score, None
        else:
            return score
    
    def evaluate_relative(self, board):
        """Evaluate a position and return the relative score"""
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(**self.config))

        possible_mate_score = str(info['score'].relative)
        if '#' in possible_mate_score:
            if '+' in possible_mate_score:
                return 10000
            else:
                return -10000

        # handle error if score is none when mate in n
        score = info['score'].relative.score()
        return score
    
    def has_mate_in_n(self, board):
        """Check if position has a mate in n moves"""
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(**self.config))

            if '#' in str(info['score'].relative):
                return True
            else:
                return False
    
    def get_best_move(self, board):
        """Get the best move in the position"""
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(**self.config))

        best_move = info['pv'][0]
        return best_move
    
    def get_best_sequence(self, board):
        """Get the best move sequence in the position"""
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(**self.config))

        best_moves = info['pv']
        return best_moves
    
    def check_for_threats(self, board, moves_ahead=2, take_turns=False, by_opponent=True):
        """Check for threats in a position"""
        assert not board.is_check()

        threat_moves = []

        opponent_color = not board.turn
        
        if take_turns:
            with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
                info = engine.analyse(board, chess.engine.Limit(**self.config))

            threat_moves = info['pv'][:moves_ahead]

        else:
            experiment_board = board.copy()
            for i in range(moves_ahead):
                experiment_board = chess.Board(experiment_board.fen())
                if by_opponent:
                    experiment_board.turn = opponent_color
                else:
                    experiment_board.turn = not opponent_color
                with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
                    info = engine.analyse(experiment_board, chess.engine.Limit(**self.config))
                
                best_move = info['pv'][0]
                threat_moves.append(best_move)
                experiment_board.push(best_move)

                if experiment_board.is_check():
                    break

        return threat_moves

# Create a global engine instance
engine = Engine()
