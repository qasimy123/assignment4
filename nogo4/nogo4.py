#!/usr/local/bin/python3
# import sys
from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY, BLACK, WHITE
from simple_board import SimpleGoBoard

# import numpy as np
# import random
import MCRave


def undo(board: SimpleGoBoard, move):
    board.board[move] = EMPTY
    board.current_player = GoBoardUtil.opponent(board.current_player)


def play_move(board: SimpleGoBoard, move, color):
    board.play_move(move, color)


def game_result(board: SimpleGoBoard):
    legal_moves = GoBoardUtil.generate_legal_moves(board, board.current_player)
    if not legal_moves:
        result = BLACK if board.current_player == WHITE else WHITE
    else:
        result = None
    return result


class NoGoFlatMC():
    def __init__(self):
        """
        NoGo player that selects moves by flat Monte Carlo Search.
        Resigns only at the end of game.
        Replace this player's algorithm by your own.

        """
        self.name = "NoBro"
        self.version = 1.0
        self.best_move = None
        self.mct = MCRave.MCTS()

    def get_move(self, original_board, color):
        """
        The genmove function using one-ply MC search.
        """
        board = original_board.copy()
        move = self.mct.get_move(
            board.copy(),
            color
        )
        self.update(move)
        return move

    def update(self, move):
        self.parent = self.mct._root
        self.mct.update_with_move(move)


def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(NoGoFlatMC(), board)
    con.start_connection()


if __name__ == '__main__':
    run()
