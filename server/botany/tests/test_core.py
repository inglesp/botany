# TODO: Once core is its own package, move these tests.  They're here currently
# so that they can be easily run by the Django test runner.

import itertools
from unittest import TestCase

from botany_noughtsandcrosses import game

from botany_core import tracer, verifier
from botany_core.runner import Result, ResultType, rerun_game, run_game


class TracerTests(TestCase):
    @staticmethod
    def f(n):
        x = 0
        for _ in range(n):
            x += 1

    def test_not_exceeding_limit(self):
        with tracer.limited_opcodes(100):
            self.f(10)

    def test_exceeding_limit(self):
        with self.assertRaises(tracer.OpCodeLimitExceeded):
            with tracer.limited_opcodes(100):
                self.f(10)
                self.f(10)

    def test_count_is_reset_on_each_call(self):
        with tracer.limited_opcodes(100):
            self.f(10)

        with tracer.limited_opcodes(100):
            self.f(10)

    def test_opcode_count(self):
        with tracer.limited_opcodes(100) as trace:
            self.f(10)

        self.assertTrue(0 < trace.opcode_count < 100)


class VerifierTests(TestCase):
    def test_valid_code(self):
        code = """
# This is a comment

import random

from botany_noughtsandcrosses import game

def get_available_moves(board):
    return game.available_moves(board)

def get_next_move(board):
    return random.choice(get_available_moves(board))
        """

        verifier.verify_bot_code(code)

    def test_code_with_syntax_error(self):
        code = """
def get_next_move()
    pass
    """

        with self.assertRaisesRegexp(verifier.InvalidBotCode, "contains a SyntaxError"):
            verifier.verify_bot_code(code)

    def test_code_with_top_level_definition(self):
        code = """
x = 123

def get_next_move(board):
    pass
        """

        with self.assertRaisesRegexp(verifier.InvalidBotCode, "not an import"):
            verifier.verify_bot_code(code)

    def test_code_with_get_next_move_missing_required_param(self):
        code = """
def get_next_move(token, state):
    pass
        """

        with self.assertRaisesRegexp(verifier.InvalidBotCode, "must have either"):
            verifier.verify_bot_code(code)

    def test_code_with_get_next_move_having_extra_param(self):
        code = """
def get_next_move(move_list, beard):
    pass
        """

        with self.assertRaisesRegexp(verifier.InvalidBotCode, "may only have"):
            verifier.verify_bot_code(code)

    def test_code_missing_get_next_move(self):
        code = """
def get_move(board):
    pass
        """

        with self.assertRaisesRegexp(verifier.InvalidBotCode, "does not define"):
            verifier.verify_bot_code(code)


class RerunGameTests(TestCase):
    def test_rerun_game(self):
        move_list = [0, 1, 2, 3, 4, 5, 6]
        boards = rerun_game(game, move_list)
        expected_boards = [
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            ["X", ".", ".", ".", ".", ".", ".", ".", "."],
            ["X", "O", ".", ".", ".", ".", ".", ".", "."],
            ["X", "O", "X", ".", ".", ".", ".", ".", "."],
            ["X", "O", "X", "O", ".", ".", ".", ".", "."],
            ["X", "O", "X", "O", "X", ".", ".", ".", "."],
            ["X", "O", "X", "O", "X", "O", ".", ".", "."],
            ["X", "O", "X", "O", "X", "O", "X", ".", "."],
        ]
        self.assertEqual(boards, expected_boards)


class RunGameTests(TestCase):
    def test_bot1_wins(self):
        # X | O | X
        # --|---|--
        # O | X | O
        # --|---|--
        # X | . | .

        result = run_game(game, get_next_move_1, get_next_move_1)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=1,
            move_list=[0, 1, 2, 3, 4, 5, 6],
            traceback=None,
        )

        self.assertEqual(result, expected_result)

    def test_bot2_wins(self):
        # . | X | O
        # --|---|--
        # X | O | X
        # --|---|--
        # O | . | .

        result = run_game(game, get_next_move_2, get_next_move_2)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=-1,
            move_list=[1, 2, 3, 4, 5, 6],
            traceback=None,
        )

        self.assertEqual(result, expected_result)

    def test_draw(self):
        # X | X | O
        # --|---|--
        # O | O | X
        # --|---|--
        # X | X | O

        result = run_game(game, get_next_move_3, get_next_move_4)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=0,
            move_list=[0, 2, 1, 3, 5, 4, 6, 8, 7],
            traceback=None,
        )

        self.assertEqual(result, expected_result)

    def test_state(self):
        # X | O | X
        # --|---|--
        # O | X | O
        # --|---|--
        # X | . | .

        result = run_game(game, get_next_move_5, get_next_move_6)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=1,
            move_list=[0, 1, 2, 3, 4, 5, 6],
            traceback=None,
        )

        self.assertEqual(result, expected_result)

    def test_all_params(self):
        # X | O | X
        # --|---|--
        # O | X | O
        # --|---|--
        # X | . | .

        result = run_game(game, get_next_move_7, get_next_move_7)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=1,
            move_list=[0, 1, 2, 3, 4, 5, 6],
            traceback=None,
        )

        self.assertEqual(result, expected_result)

    def test_invalid_move(self):
        # X | . | .
        # --|---|--
        # . | . | .
        # --|---|--
        # . | . | .

        result = run_game(game, get_next_move_1, get_next_move_8)

        expected_result = Result(
            result_type=ResultType.INVALID_MOVE, score=1, move_list=[0], traceback=None
        )

        self.assertEqual(result, expected_result)

    def test_exception(self):
        # X | . | .
        # --|---|--
        # . | . | .
        # --|---|--
        # . | . | .

        result = run_game(game, get_next_move_1, get_next_move_9)

        self.assertEqual(result.result_type, ResultType.EXCEPTION)
        self.assertEqual(result.score, 1)
        self.assertEqual(result.move_list, [0])
        self.assertIn("KeyError: 123", result.traceback)

    def test_timeout(self):
        # X | . | .
        # --|---|--
        # . | . | .
        # --|---|--
        # . | . | .

        result = run_game(game, get_next_move_1, get_next_move_10, opcode_limit=1000)

        expected_result = Result(
            result_type=ResultType.TIMEOUT, score=1, move_list=[0], traceback=None
        )

        self.assertEqual(result, expected_result)

    def test_timeout_when_opcode_limit_not_set(self):
        # X | O | X
        # --|---|--
        # O | X | O
        # --|---|--
        # X | . | .

        result = run_game(game, get_next_move_1, get_next_move_10)

        expected_result = Result(
            result_type=ResultType.COMPLETE,
            score=1,
            move_list=[0, 1, 2, 3, 4, 5, 6],
            traceback=None,
        )

        self.assertEqual(result, expected_result)


def get_next_move_1(board):
    """Return first available move."""

    available_moves = game.available_moves(board)
    return available_moves[0]


def get_next_move_2(board):
    """Return second available move."""

    available_moves = game.available_moves(board)
    return available_moves[1]


def get_next_move_3(board):
    """Return player X move to ensure draw."""

    available_moves = game.available_moves(board)
    for move in [0, 1, 5, 6, 7]:
        if move in available_moves:
            return move


def get_next_move_4(board):
    """Return player O move to ensure draw."""

    available_moves = game.available_moves(board)
    for move in [2, 3, 4, 8]:
        if move in available_moves:
            return move


def get_next_move_5(board, state):
    """Return first available move and a state.

    Also assert state is passed back to function correctly."""

    available_moves = game.available_moves(board)

    if len(available_moves) < 8:
        assert state == "Alabama"

    return available_moves[0], "Alabama"


def get_next_move_6(board, state):
    """Return first available move and a state.

    Also assert state is passed back to function correctly."""

    available_moves = game.available_moves(board)

    if len(available_moves) < 8:
        assert state == "Wyoming"

    return available_moves[0], "Wyoming"


def get_next_move_7(board, token, state, move_list):
    """Return first available move and a state.

    Also assert all params are passed in correctly."""

    assert token == game.TOKENS[len(move_list) % 2]

    board1 = game.new_board()
    for move, token in zip(move_list, itertools.cycle(game.TOKENS)):
        game.make_move(board1, move, token)

    assert board == board1

    available_moves = game.available_moves(board)

    if len(available_moves) < 8:
        assert state == "Idaho"

    return available_moves[0], "Idaho"


def get_next_move_8(board):
    """Return invalid move."""

    available_moves = game.available_moves(board)

    for move in range(9):
        if move not in available_moves:
            return move


def get_next_move_9(board):
    """Raise exception."""

    def f(n):
        if n < 0:
            return {}[123]

        return f(n - 1)

    return f(3)


def get_next_move_10(board):
    """Burn through lots of opcodes and then return first available move."""

    x = 0
    for i in range(1000):
        x += 1

    available_moves = game.available_moves(board)
    return available_moves[0]
