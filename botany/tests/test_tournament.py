from hypothesis import given
from hypothesis.extra.django import TestCase

from botany import actions, tournament

from . import factories
from . import strategies as st


class TournamentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = [factories.create_user() for _ in range(3)]

        cls.inactive_bots = [factories.create_bot(user=user) for user in users]
        cls.active_bots = [factories.create_bot(user=user) for user in users]
        for bot in cls.inactive_bots:
            bot.refresh_from_db()
        cls.bots = cls.active_bots + cls.inactive_bots

    def test_standings_with_no_games(self):
        keys = ["num_played", "num_wins", "num_draws", "num_losses", "score"]

        expected_rows = [
            [bot.id] + [0 for _ in keys]
            for bot in sorted(self.active_bots, key=lambda bot: bot.name)
        ]

        rows = [
            [getattr(bot, k) for k in ["id"] + keys] for bot in tournament.standings()
        ]

        self.assertEqual(rows, expected_rows)

    @given(st.results(num_bots=6, num_games=40))
    def test_standings(self, results):
        expected_rows_by_bot = {
            bot: {
                "num_played": 0,
                "num_wins": 0,
                "num_draws": 0,
                "num_losses": 0,
                "score": 0,
            }
            for bot in self.active_bots
        }

        for bot1_ix, bot2_ix, score in results:
            bot1 = self.bots[bot1_ix]
            bot2 = self.bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            actions.report_result(bot1.id, bot2.id, score)

            if bot1 in self.inactive_bots or bot2 in self.inactive_bots:
                continue

            row1 = expected_rows_by_bot[bot1]
            row2 = expected_rows_by_bot[bot2]

            row1["num_played"] += 1
            row2["num_played"] += 1

            if score == 1:
                row1["num_wins"] += 1
                row1["score"] += 1
                row2["num_losses"] += 1
                row2["score"] -= 1
            elif score == 0:
                row1["num_draws"] += 1
                row2["num_draws"] += 1
            elif score == -1:
                row1["num_losses"] += 1
                row1["score"] -= 1
                row2["num_wins"] += 1
                row2["score"] += 1
            else:
                assert False

        bots = []
        keys = ["num_played", "num_wins", "num_draws", "num_losses", "score"]

        for bot, row in expected_rows_by_bot.items():
            for k in keys:
                setattr(bot, k, row[k])
            bots.append(bot)

        def sortkey(bot):
            return [-bot.score, bot.num_played, -bot.num_wins, bot.name]

        sorted_bots = sorted(bots, key=sortkey)

        expected_rows = [
            [getattr(bot, k) for k in ["id"] + keys] for bot in sorted_bots
        ]

        rows = [
            [getattr(bot, k) for k in ["id"] + keys] for bot in tournament.standings()
        ]

        self.assertEqual(rows, expected_rows)

    @given(st.results(num_bots=6, num_games=40))
    def test_standings_against_bot(self, results):
        this_bot = self.active_bots[0]

        expected_rows_by_bot = {
            bot: {
                "num_played": 0,
                "num_wins": 0,
                "num_draws": 0,
                "num_losses": 0,
                "score": 0,
            }
            for bot in self.active_bots
        }

        for bot1_ix, bot2_ix, score in results:
            bot1 = self.bots[bot1_ix]
            bot2 = self.bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            actions.report_result(bot1.id, bot2.id, score)

            if bot1 in self.inactive_bots or bot2 in self.inactive_bots:
                continue

            if this_bot not in [bot1, bot2]:
                continue

            row1 = expected_rows_by_bot[bot1]
            row2 = expected_rows_by_bot[bot2]

            row1["num_played"] += 1
            row2["num_played"] += 1

            if score == 1:
                row1["num_wins"] += 1
                row1["score"] += 1
                row2["num_losses"] += 1
                row2["score"] -= 1
            elif score == 0:
                row1["num_draws"] += 1
                row2["num_draws"] += 1
            elif score == -1:
                row1["num_losses"] += 1
                row1["score"] -= 1
                row2["num_wins"] += 1
                row2["score"] += 1
            else:
                assert False

        bots = []
        keys = ["num_played", "num_wins", "num_draws", "num_losses", "score"]

        for bot, row in expected_rows_by_bot.items():
            if bot == this_bot:
                continue

            for k in keys:
                setattr(bot, k, row[k])
            bots.append(bot)

        def sortkey(bot):
            return [-bot.score, bot.num_played, -bot.num_wins, bot.name]

        sorted_bots = sorted(bots, key=sortkey)

        expected_rows = [
            [getattr(bot, k) for k in ["id"] + keys] for bot in sorted_bots
        ]

        rows = [
            [getattr(bot, k) for k in ["id"] + keys]
            for bot in tournament.standings_against_bot(this_bot)
        ]

        self.assertEqual(rows, expected_rows)

    @given(st.results(num_bots=6, num_games=40))
    def test_unplayed_games_for_bot_when_bot_active(self, results):
        bot = self.active_bots[0]
        unplayed_games = {}

        for other_bot in self.active_bots[1:]:
            unplayed_games[(bot.id, other_bot.id)] = 5
            unplayed_games[(other_bot.id, bot.id)] = 5

        for bot1_ix, bot2_ix, score in results:
            bot1 = self.bots[bot1_ix]
            bot2 = self.bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            actions.report_result(bot1.id, bot2.id, score)

            if not (bot1.is_active and bot2.is_active):
                continue

            if bot1 == bot or bot2 == bot:
                unplayed_games[(bot1.id, bot2.id)] -= 1

        unplayed_games = {
            ids: count for ids, count in unplayed_games.items() if count > 0
        }

        self.assertEqual(tournament.unplayed_games_for_bot(bot), unplayed_games)

    def test_unplayed_games_for_new_bot(self):
        bot = self.active_bots[0]

        unplayed_games = {}
        for other_bot in self.active_bots[1:]:
            unplayed_games[(bot.id, other_bot.id)] = 5
            unplayed_games[(other_bot.id, bot.id)] = 5

        self.assertEqual(tournament.unplayed_games_for_bot(bot), unplayed_games)

    def test_unplayed_games_for_bot_when_bot_not_active(self):
        bot = self.inactive_bots[0]
        self.assertEqual(tournament.unplayed_games_for_bot(bot), {})

    @given(st.results(num_bots=6, num_games=40))
    def test_all_unplayed_games(self, results):
        unplayed_games = {}

        for bot1 in self.active_bots:
            for bot2 in self.active_bots:
                if bot1 == bot2:
                    continue

                unplayed_games[(bot1.id, bot2.id)] = 5

        for bot1_ix, bot2_ix, score in results:
            bot1 = self.bots[bot1_ix]
            bot2 = self.bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            actions.report_result(bot1.id, bot2.id, score)

            if not (bot1.is_active and bot2.is_active):
                continue

            unplayed_games[(bot1.id, bot2.id)] -= 1

        unplayed_games = {
            ids: count for ids, count in unplayed_games.items() if count > 0
        }

        self.assertEqual(tournament.all_unplayed_games(), unplayed_games)
