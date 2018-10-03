import io
import contextlib
import pathlib
import zipfile

from django.test import TestCase

from botany import actions
from botany import download as botany_download
from botany.tests import factories


class DownloadBotCodeTest(TestCase):

    def setUp(self):
        self.zip_path = pathlib.Path.cwd() / "test_bots.zip"

        self.randobot_code = factories.bot_code("randobot")
        # House bots should be downloaded
        factories.create_house_bot("randobot.py", self.randobot_code)

        self.anne = factories.create_user("anne@example.com", "Anne Example")
        # Will be marked inactive once 2nd annes_bot is active, so should not be
        # downloaded
        factories.create_bot(self.anne, "annes_bot.py", "# Anne's bot code")
        # Should be downloaded
        factories.create_bot(self.anne, "annes_bot.py", "# Anne's bot code mk2")

        brad = factories.create_user("brad@example.com", "Brad Example")
        brads_code = "def get_next_move(board):\n    return 0"
        # Failed so should not be downloaded
        brads_bot = factories.create_bot(
            brad, "brads_bot.py", brads_code, "probation")
        actions.mark_bot_failed(brads_bot)

        cara = factories.create_user("cara@example.com", "Cara Example")
        # On probation so should not be downloaded
        factories.create_bot(cara, "caras_bot.py", "# Cara's bot", "probation")

        self.dave = factories.create_user("dave@example.com", "Dave Example")
        # Set active so should be downloaded
        factories.create_bot(self.dave, "daves-bot.py", "# Dave's bot")

        self.dummy_bots = [
            (
                "randobot.py",
                self.randobot_code
            ),
            (
                "annes_bot.py",
                "# Anne's bot code mk2"
            ),
            (
                "daves-bot.py",
                "# Dave's bot"
            )
        ]

    def test_download_active_bots_opens_in_memory(self):
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
        result = botany_download.get_active_bots()

        # save to disk
        with open(self.zip_path, "wb") as zf:
            zf.write(result.getvalue())

        # open from disk
        with zipfile.ZipFile(self.zip_path, "r") as zip_file:

            self.assertIsInstance(zip_file, zipfile.ZipFile)
            self.assertCountEqual(
                zip_file.namelist(),
                list(bot[0] for bot in self.dummy_bots)
            )

            for filename, code in self.dummy_bots:
                with zip_file.open(filename) as code_bytes:
                    self.assertMultiLineEqual(
                        io.TextIOWrapper(code_bytes).read(), code)

    def test_get_active_bots_for_api(self):
        result = botany_download.get_active_bots_for_api()

        self.assertEqual(len(self.dummy_bots), len(result))

        for (filename, code), bot in zip(self.dummy_bots, result):
            self.assertEqual(bot["name"], filename)
            self.assertMultiLineEqual(bot["code"], code)

    def test_get_bots(self):
        bots = botany_download.get_bots()

        self.assertTrue(hasattr(bots, "__iter__"))

        default_maxDiff = self.maxDiff
        self.maxDiff = None

        self.assertCountEqual(self.dummy_bots, bots)
        self.maxDiff = default_maxDiff

    def test_get_bots_renames_duplicates(self):
        annes_bot3 = factories.create_bot(
            self.anne,
            "randobot.py",
            "# Anne's bot mk3"
        )
        daves_bot2 = factories.create_bot(
            self.dave,
            "randobot.py",
            "# Dave's 2nd bot"
        )

        bots = botany_download.get_bots()

        # finally do some testing
        self.assertTrue(hasattr(bots, "__iter__"))

        default_maxDiff = self.maxDiff
        self.maxDiff = None

        self.assertCountEqual([
            ("randobot.py", self.randobot_code),
            ("randobot (1).py", "# Anne's bot mk3"),
            ("randobot (2).py", "# Dave's 2nd bot"),
        ], bots)
        self.maxDiff = default_maxDiff

    def tearDown(self):
        # Delete the zip file created in one of the tests,
        # whether test fails or passes
        with contextlib.suppress(FileNotFoundError):
            self.zip_path.unlink()
