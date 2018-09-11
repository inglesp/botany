import random

from noughtsandcrosses import game


def get_next_move(board, token):
    available_moves = game.available_moves(board)

    if token == "O":
        for move in range(9):
            if move not in available_moves:
                return move

    return random.choice(available_moves)
