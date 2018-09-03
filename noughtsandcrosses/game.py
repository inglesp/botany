# This is an example game module, also used in tests.

TOKENS = ["X", "O"]
EMPTY = "."

LINES_OF_3 = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
]


def new_board():
    return [EMPTY] * 9


def make_move(board, pos, token):
    assert is_valid_move(board, pos)
    board[pos] = token


def available_moves(board):
    return [pos for pos, token in enumerate(board) if token == EMPTY]


def is_valid_move(board, pos):
    return board[pos] == EMPTY


def check_winner(board):
    for line in LINES_OF_3:
        if board[line[0]] == EMPTY:
            continue

        if board[line[0]] == board[line[1]] == board[line[2]]:
            return board[line[0]]

    return None
