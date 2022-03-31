"""
feature_moves.py
Move generation based on simple features.
"""

# from random import randint, random
from board_score import winner
from board_util import GoBoardUtil, PASS
from patternbasedfeatures import get_pattern_based_feature_move
from simple_board import SimpleGoBoard
# import numpy as np
# import random
import sys


class FeatureMoves(object):
    @staticmethod
    def playGame(board: SimpleGoBoard, color, limit, use_pattern=False):
        board = board.copy()
        for _ in range(limit):
            color = board.current_player
            # move = GoBoardUtil.generate_random_move(board, color, False)
            if use_pattern:
                move = get_pattern_based_feature_move(board, color)
                if not move:
                    move = GoBoardUtil.generate_random_move(
                        board, color, False)
            else:
                move = GoBoardUtil.generate_random_move(board, color, False)

            if move == PASS:
                break
            board.play_move(move, color)

        w = winner(board)
        sys.stderr.write("Winner: {}\n".format(w))
        return w
