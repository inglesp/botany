from django.test import TestCase, override_settings

from botany import actions, models, scheduler
from core.runner import Result, ResultType

from . import factories


class CreateUserTests(TestCase):
    def test_create_user(self):
        user = actions.create_user("alice@example.com", "Alice Apple")

        self.assertEqual(user.email_addr, "alice@example.com")
        self.assertEqual(user.name, "Alice Apple")
        self.assertEqual(len(user.api_token), 12)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_superuser)


class DeactivateUserTests(TestCase):
    def test_deactivate_user(self):
        user = factories.create_user(num_bots=2)

        actions.deactivate_user(user)

        self.assertFalse(user.is_active)
        self.assertIsNone(user.active_bot)
        for bot in user.bots.all():
            self.assertFalse(bot.is_active)


class CreateHouseBotTests(TestCase):
    def test_create_house_bot(self):
        code = factories.bot_code("randobot")

        bot = actions.create_house_bot("randobot", code)

        self.assertEqual(bot.user, None)
        self.assertEqual(bot.name, "randobot")
        self.assertEqual(bot.code, code)
        self.assertTrue(bot.is_house_bot)


class CreateBotTests(TestCase):
    def test_create_bot(self):
        user = factories.create_user()
        code = factories.bot_code("randobot")

        bot = actions.create_bot(user, "randobot", code)

        self.assertEqual(bot.user, user)
        self.assertEqual(bot.name, "randobot")
        self.assertEqual(bot.code, code)
        self.assertTrue(bot.is_under_probation)
        self.assertEqual(user.active_bot, bot)


class SetBotActiveTests(TestCase):
    def test_set_bot_active(self):
        user = factories.create_user(num_bots=2)
        bot1, bot2 = user.bots.order_by("id")
        self.assertFalse(bot1.is_active)
        self.assertTrue(bot2.is_active)

        actions.set_bot_active(bot1)

        bot1.refresh_from_db()
        bot2.refresh_from_db()

        self.assertTrue(bot1.is_active)
        self.assertFalse(bot2.is_active)


class MarkBotAsFailedTests(TestCase):
    def test_mark_bot_as_failed(self):
        bot = factories.create_bot(state="probation")

        actions.mark_bot_failed(bot)

        bot.refresh_from_db()

        self.assertTrue(bot.is_failed)


@override_settings(USE_QUEUES=True)
class ScheduleGamesAgainstHouseBotsTests(TestCase):
    def test_schedule_games_against_house_bots(self):
        bot = factories.create_bot(state="probation")

        scheduler.clear_queues()

        actions.schedule_games_against_house_bots(bot)

        queue = scheduler.get_house_queue()
        self.assertEqual(len(queue.jobs), 1)


@override_settings(USE_QUEUES=True)
class ScheduleUnplayedGamesForBotTests(TestCase):
    def test_schedule_unplayed_games_for_bot(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]
        factories.report_result(bot1.id, bot2.id, 1)
        factories.report_result(bot1.id, bot2.id, -1)
        factories.report_result(bot2.id, bot1.id, 1)

        scheduler.clear_queues()

        actions.schedule_unplayed_games_for_bot(bot1)

        queue = scheduler.get_main_queue()
        self.assertEqual(len(queue.jobs), 7)


@override_settings(USE_QUEUES=True)
class ScheduleAllUnplayedGamesTests(TestCase):
    def test_schedule_unplayed_games_for_bot(self):
        bot1, bot2, bot3 = [factories.create_bot() for _ in range(3)]
        factories.report_result(bot1.id, bot2.id, 1)
        factories.report_result(bot1.id, bot2.id, -1)
        factories.report_result(bot1.id, bot3.id, 1)
        factories.report_result(bot1.id, bot3.id, -1)
        factories.report_result(bot2.id, bot1.id, 1)
        factories.report_result(bot3.id, bot1.id, 1)

        scheduler.clear_queues()

        actions.schedule_all_unplayed_games()

        queue = scheduler.get_main_queue()
        self.assertEqual(len(queue.jobs), 24)


class PlayGamesAgainstHouseBotsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        factories.create_house_bot()
        factories.create_house_bot()

    def test_play_games_against_house_bots_with_good_bot(self):
        code = factories.bot_code("randobot")
        bot = factories.create_bot(code=code, state="probation")

        actions.play_games_against_house_bots(bot.id)

        bot.refresh_from_db()

        self.assertEqual(models.Game.objects.count(), 20)
        self.assertTrue(bot.is_active)

    def test_play_games_against_house_bots_with_bad_bot(self):
        code = factories.bot_code("invalid_when_playing_second")
        bot = factories.create_bot(code=code, state="probation")

        actions.play_games_against_house_bots(bot.id)

        bot.refresh_from_db()

        self.assertEqual(models.Game.objects.count(), 2)
        self.assertTrue(bot.is_failed)


class PlayGameAndReportResultTests(TestCase):
    def test_play_game_and_report_results(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        actions.play_game_and_report_result(bot1.id, bot2.id)

        models.Game.objects.get(bot1_id=bot1.id, bot2_id=bot2.id)


class PlayGameTests(TestCase):
    def test_play_game(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        result = actions.play_game(bot1.id, bot2.id)

        self.assertEqual(result.result_type, ResultType.COMPLETE)


class ReportResultTest(TestCase):
    def test_report_result(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        def build_result(score):
            return Result(
                result_type=ResultType.COMPLETE,
                score=score,
                move_list=[0, 1, 4, 7, 8],
                traceback=None,
            )

        actions.report_result(bot1.id, bot2.id, build_result(1))

        game = models.Game.objects.get()

        self.assertEqual(game.bot1_id, bot1.id)
        self.assertEqual(game.bot2_id, bot2.id)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.moves, "01478")

        actions.report_result(bot1.id, bot2.id, build_result(-1))
        actions.report_result(bot2.id, bot1.id, build_result(1))
        actions.report_result(bot2.id, bot1.id, build_result(0))

        self.assertEqual(bot1.bot1_games.count(), 2)
        self.assertEqual(bot1.bot2_games.count(), 2)

        self.assertEqual(bot1.score, -1)
        self.assertEqual(bot2.score, 1)
