# TODO:
#
# * Validate that move is valid
# * Handle exceptions in functions
# * Ensure functions don't overspend opcodes

# TODONE:
# * Capture list of moves
# * Allow functions to return state
# * Pass some of:
#     * board (copy)
#     * move_list (copy)
#     * token
#     * state
#   to functions, depending on function signature

import inspect
import itertools
from copy import copy, deepcopy
from enum import Enum, auto

import attr

VALID_PARAMS = ["board", "move_list", "token", "state"]


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

    # TODO move game validation elsewhere?
    assert len(game.TOKENS) == 2

    param_lists = [get_param_list(fn1), get_param_list(fn2)]
    states = [None, None]
    winning_scores = [1, -1]
    losing_scores = [-1, 1]
    board = game.new_board()
    move_list = []

    for player_ix in itertools.cycle([0, 1]):
        token = game.TOKENS[player_ix]
        fn = [fn1, fn2][player_ix]

        available_moves = game.available_moves(board)
        if available_moves == []:
            return build_result(ResultType.COMPLETE, 0)

        all_args = {
            "board": deepcopy(board),
            "move_list": copy(move_list),
            "token": token,
            "state": states[player_ix],
        }

        args = {
            param: value
            for param, value in all_args.items()
            if param in param_lists[player_ix]
        }

        rv = fn(**args)

        try:
            move, state = rv
        except TypeError:
            move, state = rv, None

        if move not in available_moves:
            return build_result(ResultType.INVALID_MOVE, losing_scores[player_ix])

        states[player_ix] = state
        move_list.append(move)

        game.make_move(board, move, token)

        winner = game.check_winner(board)
        if winner is not None:
            assert winner == token
            return build_result(ResultType.COMPLETE, winning_scores[player_ix])


def get_param_list(fn):
    # TODO move fn validation elsewhere?
    param_list = list(inspect.signature(fn).parameters)
    for param in param_list:
        assert param in VALID_PARAMS
    return param_list
