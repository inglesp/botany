# This exercises botany_noughtsandcrosses.game and allows a human to play X
# against a random O.
#
# Usage:
#
# $ python -m botany_noughtsandcrosses

import itertools
import random

from botany_noughtsandcrosses import game


def play_game(fn1, fn2):
    board = game.new_board()
    display(board)

    for token, fn in itertools.cycle(zip(game.TOKENS, [fn1, fn2])):
        available_moves = game.available_moves(board)
        if available_moves == []:
            announce_draw()
            return

        pos = fn(board)
        game.make_move(board, pos, token)
        display(board)

        winner = game.check_winner(board)
        if winner is not None:
            announce_winner(winner)
            return


def display(board):
    print()
    print(game.render_text(board))
    print()


def announce_winner(winner):
    print(f"{winner} has won")


def announce_draw():
    print("The game is a draw")


def get_next_move_human(board):
    available_moves = game.available_moves(board)

    while True:
        col = input("> ")
        try:
            col = int(col)
        except ValueError:
            continue

        if col not in available_moves:
            continue

        return col


def get_next_move_random(board):
    available_moves = game.available_moves(board)

    return random.choice(available_moves)


if __name__ == "__main__":
    play_game(get_next_move_human, get_next_move_random)
