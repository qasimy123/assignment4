#!/usr/bin/python3
"""
This function is loosely based on https://github.com/Rochester-NRT/RocAlphaGo/blob/develop/AlphaGo/mcts.py
Code modified from go5 example available on course website..
"""
import sys
import time
import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, PASS
from feature_moves import FeatureMoves
from simple_board import SimpleGoBoard
from gtp_connection import point_to_coord, format_point
from collections import defaultdict


def uct_val(node: 'TreeNode', child: 'TreeNode', exploration, max_flag):
    if child._n_visits == 0:
        return float('inf')
    
    if max_flag:
        mu_squigly = float(child._black_wins_as_result) / \
            (child._n_visits_across)
        mu_hat = float(child._black_wins)/(child._n_visits)
        
    else:
        mu_squigly = float(child._n_visits_across-20-child._black_wins_as_result) / \
            (child._n_visits_across)
        mu_hat = float(child._n_visits-child._black_wins)/(child._n_visits)
        
    Beta = np.sqrt(node.k/(3*node._n_visits+node.k))
    mu = (1-Beta)*mu_hat + Beta*mu_squigly
    return mu + exploration * np.sqrt(
        np.log(node._n_visits) / (child._n_visits)
    )


class TreeNode(object):
    moves_dict = defaultdict(set)
    """
    A node in the MCTS tree.
    """

    version = 0.22
    name = "MCTS Player"

    def __init__(self, parent):
        """
        parent is set when a node gets expanded
        """
        self._parent = parent
        self._children = {}  # a map from move to TreeNode
        self._n_visits = 0  # n
        self._black_wins = 0  # w
        self._black_wins_as_result = 0  # w with squigly
        self._n_visits_across = 20  # n with squigly
        self.mu_hat = 0.5
        self.mu_squigly = 0.5
        self.k = 100
        self._expanded = False
        self._move = None

    def expand(self, board: SimpleGoBoard, color):
        """
        Expands tree by creating new children.
        """
        moves = GoBoardUtil.generate_legal_moves(board, board.current_player)
        for move in moves:
            if move not in self._children:
                # sys.stderr.write("expand: move = {}\n".format(move))
                self._children[move] = TreeNode(self)
                self._children[move]._move = move
                TreeNode.moves_dict[color].add(move)
        self._expanded = True

    def select(self, exploration, max_flag):
        """
        Select move among children that gives maximizes UCT. 
        If number of visits are zero for a node, value for that node is infinite, so definitely will get selected

        It uses: argmax(child_num_black_wins/child_num_vists + C * sqrt(2 * ln * Parent_num_vists/child_num_visits) )
        Returns:
        A tuple of (move, next_node)
        """
        color = BLACK if max_flag else WHITE
        best = max(
            self._children.items(),
            key=lambda items: uct_val(
                self, items[1], exploration, max_flag),
        )
        
        # sys.stderr.write("select: best = {}\n".format(best))
        TreeNode.moves_dict[color].add(best[0])
        return best

    def update(self, leaf_value):
        """
        Update node values from leaf evaluation.
        Arguments:
        leaf_value -- the value of subtree evaluation from the current player's perspective.

        Returns:
        None
        """
        # sys.stderr.write("update: leaf_value = {}\n".format(leaf_value))
        self._black_wins += leaf_value
        self._n_visits += 1
        # self._black_wins_as_result += leaf_value
        # self._n_visits_across += 1

    def update_recursive(self, leaf_value, color):
        """
        Like a call to update(), but applied recursively for all ancestors.

        Note: it is important that this happens from the root downward so that 'parent' visit
        counts are correct.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            for key, value in self._parent._children.items():
                if key in TreeNode.moves_dict[color] and value!=self:
                    value: TreeNode
                    value._n_visits_across += 1
                    value._black_wins_as_result += leaf_value
            self._parent.update_recursive(
                leaf_value, GoBoardUtil.opponent(color))
        self.update(leaf_value)

    def is_leaf(self):
        """
        Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def is_root(self):
        return self._parent is None


class MCTS(object):
    def __init__(self):
        self._root = TreeNode(None)
        self.toplay = BLACK
        self.exploration = 0.4
        self.limit = 200
        self.komi = 6.5
        self.num_simulation = 1000
        self.use_pattern = False

    def _playout(self, board: SimpleGoBoard, color):
        """
        Run a single playout from the root to the given depth, getting a value at the leaf and
        propagating it back through its parents. State is modified in-place, so a copy must be
        provided.

        Arguments:
        board -- a copy of the board.
        color -- color to play


        Returns:
        None
        """
        # TreeNode.moves_dict.clear()
        node = self._root
        # This will be True olny once for the root
        if not node._expanded:
            # sys.stderr.write("expand: node._move = {}\n".format(node._move))
            node.expand(board, color)
        while not node.is_leaf():
            # sys.stderr.write("node._n_visits = {}\n".format(node._n_visits))
            # Greedily select next move.
            max_flag = color == BLACK
            move, next_node = node.select(self.exploration, max_flag)
            # sys.stderr.write("move = {}\n".format(move))
            if move != PASS:
                # sys.stderr.write("Testing {}\n".format(
                # board.is_legal(move, color)))
                if not board.is_legal(move, color):
                    return
                assert board.is_legal(move, color)
            if move == PASS:
                # sys.stderr.write("No way\n")
                move = None
            board.play_move(move, color)
            # TreeNode.moves_dict[color].append(move)
            color = GoBoardUtil.opponent(color)
            node = next_node
        # sys.stderr.write("1\n")
        assert node.is_leaf()
        if not node._expanded:
            # sys.stderr.write("22\n")
            node.expand(board, color)
        # sys.stderr.write("Done\n")
        assert board.current_player == color
        leaf_value = self._evaluate_rollout(board, color)
        # Update value and visit count of nodes in this traversal.
        node.update_recursive(leaf_value, color)

    def _evaluate_rollout(self, board: SimpleGoBoard, toplay):
        """
        Use the rollout policy to play until the end of the game, returning +1 if the current
        player wins, -1 if the opponent wins, and 0 if it is a tie.
        """
        winner = FeatureMoves.playGame(
            board,
            toplay,
            self.limit,
            self.use_pattern,
        )
        if winner == BLACK:
            return 1
        else:
            return 0

    def get_move(
        self,
        board: SimpleGoBoard,
        toplay
    ):
        """
        Runs all playouts sequentially and returns the most visited move.
        """
        # sys.stderr.write("MCTS: get_move\n")
        if self.toplay != toplay:
            # sys.stderr.write("Dumping the subtree! \n")
            # sys.stderr.flush()
            if board.last_move not in self._root._children:
                # sys.stderr.write("No such move!\n")
                self._root = TreeNode(None)
                TreeNode.moves_dict.clear()
            else:
                # sys.stderr.write("Found the move!\n")
                self._root = self._root._children[board.last_move]
        self.toplay = toplay
        TIME_LIMIT = 29
        # for n in range(self.num_simulation):
        #     board_copy = board.copy()
        #     self._playout(board_copy, toplay)
        i = 0
        # Rewrite forloop to use time limit
        start_time = time.time()
        curr_time = time.time()
        while curr_time - start_time < TIME_LIMIT:
            board_copy = board.copy()
            self._playout(board_copy, toplay)
            curr_time = time.time()
            i += 1
        # sys.stderr.write("MCTS: {} playouts\n".format(i))
        
        # choose a move that has the most visit
        # sys.stderr.write("Root children = {}\n".format(self._root._children))
        moves_ls = [
            (move, node._n_visits) for move, node in self._root._children.items()
        ]
        # sys.stderr.write("moves_ls = {}\n".format(moves_ls))
        # sys.stderr.write("moves_ls = {}\n".format(moves_ls))
        if not moves_ls:
            return None
        moves_ls = sorted(moves_ls, key=lambda i: i[1], reverse=True)
        move = moves_ls[0]
        # self.good_print(board,self._root,self.toplay,10)
        # sys.stderr.write("Moves_ls = {}\n".format(moves_ls))
        if move[0] == PASS:
            return None
        assert board.is_legal(move[0], toplay)
        return move[0]

    def update_with_move(self, last_move):
        """
        Step forward in the tree, keeping everything we already know about the subtree, assuming
        that get_move() has been called already. Siblings of the new root will be garbage-collected.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
        else:
            self._root = TreeNode(None)
        self._root._parent = None
        self.toplay = GoBoardUtil.opponent(self.toplay)
