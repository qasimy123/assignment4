"""
feature_moves.py
Move generation based on simple features.
"""

from board_score import winner
from board_util import GoBoardUtil, PASS
from patternbasedfeatures import get_pattern_based_feature_move
from simple_board import SimpleGoBoard
# import numpy as np
# import random
import sys

class FeatureMoves(object):
    @staticmethod
    def playGame(board: SimpleGoBoard, color, limit, komi):
        # board = board.copy()
        for i in range(limit):
            color = board.current_player
            move = GoBoardUtil.generate_random_move(board, color, False)
            # sys.stderr.write("Move\n")
            # move = get_pattern_based_feature_move(board, color)
            # sys.stderr.write("Move {}".format(move))
            if move == PASS:
                break
            board.play_move(move, color)
        
        w = winner(board, komi)
        # sys.stderr.write("Winner: {}\n".format(w))
        return w
