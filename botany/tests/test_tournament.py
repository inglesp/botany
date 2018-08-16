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
        cls.bots = cls.active_bots + cls.inactive_bots

    def test_calculate_standings_with_no_games(self):
        keys = ["num_played", "num_wins", "num_draws", "num_losses", "score"]

        expected_rows = [
            [bot.id] + [0 for _ in keys]
            for bot in sorted(self.active_bots, key=lambda bot: bot.name)
        ]

        rows = [
            [getattr(bot, k) for k in ["id"] + keys]
            for bot in tournament.calculate_standings()
        ]

        self.assertEqual(rows, expected_rows)

    @given(st.results(num_bots=6, num_games=40))
    def test_calculate_standings(self, results):
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
            [getattr(bot, k) for k in ["id"] + keys]
            for bot in tournament.calculate_standings()
        ]

        self.assertEqual(rows, expected_rows)
