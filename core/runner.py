# TODO:
#
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

# TODONE:
# * Capture list of moves

import itertools
from enum import Enum, auto

import attr


class ResultType(Enum):
    COMPLETE = auto()  # The game was played to completion
    INVALID_MOVE = auto()  # The losing player made an invalid move
    EXCEPTION = auto()  # The losing player's code raised an exception
    TIMEOUT = auto()  # The losing player's code used too many opcodes


@attr.s
class Result:
    result_type = attr.ib()
    score = attr.ib()
    move_list = attr.ib()
    traceback = attr.ib()


def run_game(game, fn1, fn2):
    def build_result(result_type, score, traceback=None):
        return Result(
            result_type=result_type,
            score=score,
            move_list=move_list,
            traceback=traceback,
        )

    assert len(game.TOKENS) == 2

    board = game.new_board()
    move_list = []

    for token, fn in itertools.cycle(zip(game.TOKENS, [fn1, fn2])):
        available_moves = game.available_moves(board)
        if available_moves == []:
            return build_result(ResultType.COMPLETE, 0)

        move = fn(board)
        move_list.append(move)

        game.make_move(board, move, token)

        winner = game.check_winner(board)
        if winner == game.TOKENS[0]:
            return build_result(ResultType.COMPLETE, 1)
        elif winner == game.TOKENS[1]:
            return build_result(ResultType.COMPLETE, -1)
