import random

from botany_noughtsandcrosses import game


def get_next_move(board):
    available_moves = game.available_moves(board)
    return random.choice(available_moves)
