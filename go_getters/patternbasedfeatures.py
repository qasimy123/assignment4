import sys
from simple_board import SimpleGoBoard
from collections import defaultdict
file_lines = None
from weights import weights

def init():
    
    global file_lines
    file_lines = list(enumerate(weights.strip().split('\n')))
    dict_lines = defaultdict(set)
    for i, line in file_lines:
        dict_lines[i].add(line[:-1])
    # sys.stderr.write("File lines:{}\n".format(len(dict_lines.keys())))
    file_lines = dict_lines


def get_pattern_weights(board, moves, color):
    # This function takes all current legal moves and gets the mini 3x3
    # positions around it
    global file_lines
    small_boards = get_small_boards(board, moves)

    weights = get_weights(small_boards)
    lines = []

    # with open("weights.txt") as f:
    #     for i, line in enumerate(f):
    #         if i in weights:
    #             lines.append(line[:-1])
    # sys.stderr.write("ss\n")
    # sys.stderr.write("File lineas:{}\n".format(len(file_lines.keys())))
    try:
        for i in weights:
            lines = lines+list(file_lines[i])
    except Exception as e:
        sys.stderr.write("Error: {} {} \n".format(e, file_lines))
    # sys.stderr.write("lineas:{}\n".format(lines))
    total = 0
    d_split = dict(s.split(' ') for s in lines)
    d = {int(k): float(v) for k, v in d_split.items()}
    for weight in weights:
        total += d[weight]

    # we can now return the weights we want
    return(weights, d, total)


def get_weights(boards):
    # returning weights in baseten
    weights = []
    for board in boards:
        tmp = ''
        for b in board:
            tmp += str(b)
        weights.append(tmp)
    base_ten = []

    for weight in weights:
        b_ten = 0
        for i in range(0, len(weight)):
            b_ten += int(weight[i]) * (4**(7-i))
        base_ten.append(b_ten)

    return base_ten


def get_neighbors(board: SimpleGoBoard, point):
    # from board.py
    return [point - board.NS + 1,  point - board.NS,
            point - board.NS - 1,
            point + 1, point-1, point + board.NS + 1,
            point + board.NS, point + board.NS - 1]


def get_small_boards(board: SimpleGoBoard, moves):
    # get a small board i.e. 3x3 board around an empty point
    small_boards = []
    for point in moves:
        small_boards.append(board.board[get_neighbors(board, point)])
    return small_boards


def get_pattern_based_feature_moves(board: SimpleGoBoard, color):

    empty_points = board.get_empty_points()
    moves = []
    for point in empty_points:
        if board.is_legal(point, color):
            moves.append(point)
    if not moves:
        return None

    (weights, d, weight_total) = get_pattern_weights(board, moves, color)

    result_dict = {}
    for i in range(len(moves)):
        result_dict[moves[i]] = d[weights[i]]/weight_total
    return result_dict


def get_pattern_based_feature_move(board: SimpleGoBoard, color):
    # sys.stderr.write("Test1\n")
    moves_dict = get_pattern_based_feature_moves(board, color)
    if moves_dict is None:
        return None
    best = max(moves_dict, key=moves_dict.get)
    return best
