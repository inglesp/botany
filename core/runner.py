# TODO:
#
# * Capture list of moves
# * Allow functions to return state
# * Pass some of:
#     * board (copy)
#     * move_list (copy)
#     * token
#     * state
#   to functions, depending on function signature
# * Validate that move is valid
# * Handle exceptions in functions
# * Ensure functions don't overspend opcodes

import itertools


def run_game(game, fn1, fn2):
    assert len(game.TOKENS) == 2

    board = game.new_board()

    for token, fn in itertools.cycle(zip(game.TOKENS, [fn1, fn2])):
        available_moves = game.available_moves(board)
        if available_moves == []:
            return 0

        move = fn(board)

        game.make_move(board, move, token)

        winner = game.check_winner(board)
        if winner == game.TOKENS[0]:
            return 1
        elif winner == game.TOKENS[1]:
            return -1
