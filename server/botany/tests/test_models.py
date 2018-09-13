from hypothesis import given
from hypothesis.extra.django import TestCase

from . import factories
from . import strategies as st


class BotTests(TestCase):
    @given(st.results(num_bots=3, num_games=20))
    def test_score_etc(self, results):
        bots = [factories.create_bot() for _ in range(3)]

        expected_scores = {bot: 0 for bot in bots}
        expected_nums_played = {bot: 0 for bot in bots}
        expected_nums_wins = {bot: 0 for bot in bots}
        expected_nums_draws = {bot: 0 for bot in bots}
        expected_nums_losses = {bot: 0 for bot in bots}

        for bot1_ix, bot2_ix, score in results:
            bot1 = bots[bot1_ix]
            bot2 = bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            expected_scores[bot1] += score
            expected_scores[bot2] -= score

            expected_nums_played[bot1] += 1
            expected_nums_played[bot2] += 1

            if score == 1:
                expected_nums_wins[bot1] += 1
                expected_nums_losses[bot2] += 1
            elif score == 0:
                expected_nums_draws[bot1] += 1
                expected_nums_draws[bot2] += 1
            elif score == -1:
                expected_nums_losses[bot1] += 1
                expected_nums_wins[bot2] += 1
            else:
                assert False

            factories.report_result(bot1.id, bot2.id, score)

        for bot in bots:
            self.assertEqual(bot.score, expected_scores[bot])
            self.assertEqual(bot.num_played, expected_nums_played[bot])
            self.assertEqual(bot.num_wins, expected_nums_wins[bot])
            self.assertEqual(bot.num_draws, expected_nums_draws[bot])
            self.assertEqual(bot.num_losses, expected_nums_losses[bot])
