import io
import contextlib
import pathlib
from unittest.mock import patch
import zipfile

from django.test import TestCase

from botany import actions
from botany import download as botany_download
from botany.tests import factories


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

        self.dummy_bots = [
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
        with patch("botany.download.get_bots") as patched_get_bots:
            patched_get_bots.return_value = self.dummy_bots

            result = botany_download.get_active_bots()

        # read result (BytesIO buffer) as ZipFile object
        with zipfile.ZipFile(result, "r") as zip_file:

            self.assertIsInstance(zip_file, zipfile.ZipFile)
            self.assertEqual(
                zip_file.namelist(),
                list(bot[0] for bot in self.dummy_bots)
            )

            for filename, code in self.dummy_bots:
                with zip_file.open(filename) as code_bytes:
                    self.assertMultiLineEqual(
                        io.TextIOWrapper(code_bytes).read(), code)

    def test_download_active_bots_saves_as_zip_file(self):
        with patch("botany.download.get_bots") as patched_get_bots:
            patched_get_bots.return_value = self.dummy_bots

            result = botany_download.get_active_bots()

        # save to disk
        with open(self.zip_path, "wb") as zf:
            zf.write(result.getvalue())

        # open from disk
        with zipfile.ZipFile(self.zip_path, "r") as zip_file:

            self.assertIsInstance(zip_file, zipfile.ZipFile)
            self.assertEqual(
                zip_file.namelist(),
                list(bot[0] for bot in self.dummy_bots)
            )

            for filename, code in self.dummy_bots:
                with zip_file.open(filename) as code_bytes:
                    self.assertMultiLineEqual(
                        io.TextIOWrapper(code_bytes).read(), code)

    def test_get_active_bots_for_api(self):
        with patch("botany.download.get_bots") as patched_get_bots:
            patched_get_bots.return_value = self.dummy_bots

            result = botany_download.get_active_bots_for_api()

        self.assertEqual(len(self.dummy_bots), len(result))

        for (filename, code), bot in zip(self.dummy_bots, result):
            self.assertEqual(bot["name"], filename)
            self.assertMultiLineEqual(bot["code"], code)

    def test_get_bots(self):
        anne = factories.create_user("anne@example.com", "Anne Example")
        brad = factories.create_user("brad@example.com", "Brad Example")
        cara = factories.create_user("cara@example.com", "Cara Example")
        dave = factories.create_user("dave@example.com", "Dave Example")

        # House bots should be downloaded
        factories.create_house_bot(
            "centrist.py",
            self.centrist_code,
        )

        # Will be marked inactive once annes_bot2 is active, so should not be
        # downloaded
        annes_bot1 = factories.create_bot(
            anne,
            "annes_bot.py",
            self.centrist_code
        )
        # Should be downloaded
        annes_bot2 = factories.create_bot(
            anne,
            "annes_bot.py",
            self.opportunist_code
        )

        # Failed so should not be downloaded
        brads_bot = factories.create_bot(
            brad,
            "brads_bot.py",
            self.bad_code,
            "probation",
        )
        actions.mark_bot_failed(brads_bot)

        # On probation so should not be downloaded
        factories.create_bot(
            cara,
            "caras_bot.py",
            self.anarchist_code,
            "probation",
        )

        # Set active so should be downloaded
        daves_bot = factories.create_bot(
            dave,
            "daves-bot.py",
            self.antagonist_code,
        )

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
        factories.create_house_bot(
            "centrist.py",
            self.centrist_code,
        )
        anne = factories.create_user("anne@example.com", "Anne Example")
        annes_bot = factories.create_bot(
            anne,
            "centrist.py",
            self.centrist_code
        )
        brad = factories.create_user("brad@example.com", "Brad Example")
        brads_bot = factories.create_bot(
            brad,
            "centrist.py",
            self.centrist_code
        )

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
