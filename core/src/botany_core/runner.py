import inspect
import itertools
import traceback
from copy import copy, deepcopy
from enum import Enum, auto

import attr

from .tracer import OpCodeLimitExceeded, limited_opcodes

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

    @property
    def is_complete(self):
        return self.result_type == ResultType.COMPLETE


def rerun_game(game, move_list):
    boards = [game.new_board()]

    for token, move in zip(itertools.cycle(game.TOKENS), move_list):
        board = deepcopy(boards[-1])
        available_moves = game.available_moves(board)
        assert move in available_moves
        game.make_move(board, move, token)
        boards.append(board)

    return boards


def run_game(game, fn1, fn2, opcode_limit=None, display_board=False):
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

    if display_board:
        print(game.render_text(board))

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

        try:
            if opcode_limit is None:
                rv = fn(**args)
            else:
                with limited_opcodes(opcode_limit):
                    rv = fn(**args)
        except OpCodeLimitExceeded:
            return build_result(ResultType.TIMEOUT, losing_scores[player_ix])
        except Exception:
            return build_result(
                ResultType.EXCEPTION, losing_scores[player_ix], traceback.format_exc()
            )

        try:
            move, state = rv
        except TypeError:
            move, state = rv, None

        if move not in available_moves:
            return build_result(ResultType.INVALID_MOVE, losing_scores[player_ix])

        states[player_ix] = state
        move_list.append(move)

        game.make_move(board, move, token)

        if display_board:
            print(game.render_text(board))

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
