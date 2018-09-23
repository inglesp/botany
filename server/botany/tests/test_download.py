import io
import contextlib
import pathlib
from unittest.mock import patch
import zipfile

from django.test import TestCase

from botany import actions
from botany import download as botany_download


class DownloadBotCodeTest(TestCase):

    def setUp(self):
        self.zip_path = pathlib.Path.cwd() / "test_bots.zip"
        self.anarchist_code = (
            "# This bot picks a move totally at random.\n\n"
            "import random\n\n"
            "from botany_connectfour import import game\n\n\n"
            "def get_next_move(board):\n"
            "    available_moves = game.available_moves(board)\n"
            "    return random.choice(available_moves)"
        )
        self.antagonist_code = (
            "# This bot looks one move ahead, and if possible it will make a "
            "move to block\n"
            "# its opponent winning.  Otherwise, it picks a move at random.\n\n"
            "import copy\nimport random\n"
            "from botany_connectfour import import game\n\n\n"
            "def get_next_move(board, token):\n"
            "    available_moves = game.available_moves(board)\n\n"
            "    if token == 'X':\n"
            "        other_token = 'O'\n"
            "    else:\n"
            "        other_token = 'X'\n\n"
            "    for col in available_moves:\n"
            "        board1 = copy.deepcopy(board)\n"
            "        game.make_move(board1, col, other_token)\n"
            "        if game.check_winner(board1) is not None:\n"
            "            return col\n"
            "    return random.choice(available_moves)"
        )
        self.centrist_code = (
            "# This bot picks the most central available move.\n"
            "from botany_connectfour import game\n\n"
            "def get_next_move(board):\n"
            "    available_moves = game.available_moves(board)\n"
            "    mid_point = len(available_moves) // 2\n"
            "    return available_moves[mid_point]"
        )
        self.opportunist_code = (
            "# This bot looks one move ahead, and will make a winning move if "
            "one is\n"
            "# available.  Otherwise, it picks a move at random.\n\n"
            "import copy\nimport random\n"
            "from botany_connectfour import import game\n\n\n"
            "def get_next_move(board, token):\n"
            "    available_moves = game.available_moves(board)\n"
            "    for col in available_moves:\n"
            "        board1 = copy.deepcopy(board)\n"
            "        game.make_move(board1, col, token)\n"
            "        if game.check_winner(board1) is not None:\n"
            "            return col\n"
            "    return random.choice(available_moves)"
        )
        self.bad_code = (
            "def get_next_move(board):\n    return 0"
        )

    def get_dummy_bots(self):
        """
        Utility to import dummy data - list of bot [filename, code]
        """
        return [
            [
                "centrist.py",
                self.centrist_code,
            ],
            [
                "a_bot.py",
                self.anarchist_code,
            ],
            [
                "another-bot.py",
                self.opportunist_code,
            ]
        ]

    def test_download_active_bots_opens_in_memory(self):
        bots = self.get_dummy_bots()
        with patch("botany.download.get_bots") as patched_get_bots:
            patched_get_bots.return_value = bots

            result = botany_download.download_active_bots()

        # read result (BytesIO buffer) as ZipFile object
        with zipfile.ZipFile(result, "r") as zip_file:

            self.assertIsInstance(zip_file, zipfile.ZipFile)
            self.assertEqual(
                zip_file.namelist(),
                list(bot[0] for bot in bots)
            )

            for filename, code in bots:
                with zip_file.open(filename) as code_bytes:
                    self.assertMultiLineEqual(
                        io.TextIOWrapper(code_bytes).read(), code)

    def test_download_active_bots_saves_as_zip_file(self):
        bots = self.get_dummy_bots()
        with patch("botany.download.get_bots") as patched_get_bots:
            patched_get_bots.return_value = bots

            result = botany_download.download_active_bots()

        # save to disk
        with open(self.zip_path, "wb") as zf:
            zf.write(result.getvalue())

        # open from disk
        with zipfile.ZipFile(self.zip_path, "r") as zip_file:

            self.assertIsInstance(zip_file, zipfile.ZipFile)
            self.assertEqual(
                zip_file.namelist(),
                list(bot[0] for bot in bots)
            )

            for filename, code in bots:
                with zip_file.open(filename) as code_bytes:
                    self.assertMultiLineEqual(
                        io.TextIOWrapper(code_bytes).read(), code)

    def test_get_bots(self):
        anne = actions.create_user("anne@example.com", "Anne Example")
        brad = actions.create_user("brad@example.com", "Brad Example")
        cara = actions.create_user("cara@example.com", "Cara Example")
        dave = actions.create_user("dave@example.com", "Dave Example")

        actions.create_house_bot(
            "centrist.py",
            self.centrist_code,
        )

        # Will be marked inactive once annes_bot2 is active, so should not be
        # downloaded
        annes_bot1 = actions.create_bot(
            anne,
            "annes_bot.py",
            self.centrist_code
        )
        actions.set_bot_active(annes_bot1, anne)
        annes_bot2 = actions.create_bot(
            anne,
            "annes_bot.py",
            self.opportunist_code
        )
        # should change annes_bot1 to inactive
        actions.set_bot_active(annes_bot2, anne)

        brads_bot = actions.create_bot(
            brad,
            "brads_bot.py",
            self.bad_code
        )
        # Mark failed so should not be be downloaded
        actions.mark_bot_failed(brads_bot)

        # On probation so should not be be downloaded
        actions.create_bot(
            cara,
            "caras_bot.py",
            self.anarchist_code
        )

        daves_bot = actions.create_bot(
            dave,
            "daves-bot.py",
            self.antagonist_code
        )
        actions.set_bot_active(daves_bot, dave)

        bots = botany_download.get_bots()

        # finally do some testing
        self.assertTrue(hasattr(bots, "__iter__"))

        default_maxDiff = self.maxDiff
        self.maxDiff = None

        self.assertCountEqual([
            ("centrist.py", self.centrist_code),
            ("annes_bot.py", self.opportunist_code),
            ("daves-bot.py", self.antagonist_code),
        ], bots)
        self.maxDiff = default_maxDiff

    def test_get_bots_renames_duplicates(self):
        actions.create_house_bot(
            "centrist.py",
            self.centrist_code,
        )
        anne = actions.create_user("anne@example.com", "Anne Example")
        annes_bot = actions.create_bot(
            anne,
            "centrist.py",
            self.centrist_code
        )
        actions.set_bot_active(annes_bot, anne)
        brad = actions.create_user("brad@example.com", "Brad Example")
        brads_bot = actions.create_bot(
            brad,
            "centrist.py",
            self.centrist_code
        )
        actions.set_bot_active(brads_bot, brad)

        bots = botany_download.get_bots()

        # finally do some testing
        self.assertTrue(hasattr(bots, "__iter__"))

        default_maxDiff = self.maxDiff
        self.maxDiff = None

        self.assertCountEqual([
            ("centrist.py", self.centrist_code),
            ("centrist (1).py", self.centrist_code),
            ("centrist (2).py", self.centrist_code),
        ], bots)
        self.maxDiff = default_maxDiff

    def tearDown(self):
        # Delete the zip file created in one of the tests,
        # whether test fails or passes
        with contextlib.suppress(FileNotFoundError):
            self.zip_path.unlink()
