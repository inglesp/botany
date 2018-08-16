from hypothesis import given
from hypothesis.extra.django import TestCase

from botany import actions

from . import factories
from . import strategies as st


class BotTests(TestCase):
    @given(st.results(num_bots=3, num_games=20))
    def test_score(self, results):
        bots = [factories.create_bot() for _ in range(3)]

        expected_scores = {bot: 0 for bot in bots}

        for bot1_ix, bot2_ix, score in results:
            bot1 = bots[bot1_ix]
            bot2 = bots[bot2_ix]

            if bot1.user == bot2.user:
                continue

            expected_scores[bot1] += score
            expected_scores[bot2] -= score

            actions.report_result(bot1.id, bot2.id, score)

        for bot in bots:
            self.assertEqual(bot.score, expected_scores[bot])
