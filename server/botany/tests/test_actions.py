from botany_core.runner import Result, ResultType
from django.test import TestCase, override_settings

from botany import actions, models, scheduler

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
        self.assertEqual(bot.version, 0)
        self.assertEqual(bot.code, code)
        self.assertTrue(bot.is_under_probation)
        self.assertEqual(user.active_bot, bot)

        bot = actions.create_bot(user, "randobot", code)

        self.assertEqual(bot.user, user)
        self.assertEqual(bot.name, "randobot")
        self.assertEqual(bot.version, 1)


class SetBotActiveTests(TestCase):
    def test_set_bot_active(self):
        user = factories.create_user(num_bots=2)
        bot1, bot2 = user.bots.order_by("id")
        bot3 = factories.create_bot(user, state="probation")
        actions.mark_bot_failed(bot3)
        bot4 = factories.create_bot(user, state="probation")

        self.assertTrue(bot1.is_inactive)
        self.assertTrue(bot2.is_active)
        self.assertTrue(bot3.is_failed)
        self.assertTrue(bot4.is_under_probation)

        actions.set_bot_active(bot1, user)

        bot1.refresh_from_db()
        bot2.refresh_from_db()
        bot3.refresh_from_db()
        bot4.refresh_from_db()

        self.assertTrue(bot1.is_active)
        self.assertTrue(bot2.is_inactive)
        self.assertTrue(bot3.is_failed)
        self.assertTrue(bot4.is_under_probation)


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


class PlayGamesBetweenHouseBotTests(TestCase):
    def test_play_games_between_house_bots(self):
        factories.create_house_bot()
        factories.create_house_bot()
        factories.create_house_bot()

        actions.play_games_between_house_bots()

        self.assertEqual(models.Game.objects.count(), 30)


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

    def test_play_game_when_all_games_played(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        for _ in range(5):
            factories.report_result(bot1.id, bot2.id, 0)

        result = actions.play_game(bot1.id, bot2.id)

        self.assertIsNone(result)


class ReportResultTest(TestCase):
    def build_result(self, score, result_type=ResultType.COMPLETE):
        if result_type == ResultType.EXCEPTION:
            traceback = "KeyError ..."
        else:
            traceback = None

        return Result(
            result_type=result_type,
            score=score,
            move_list=[0, 1, 4, 7, 8],
            traceback=traceback,
            invalid_move=None,
        )

    def test_report_result(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        actions.report_result(bot1.id, bot2.id, self.build_result(1))

        game = models.Game.objects.get()

        self.assertEqual(game.bot1_id, bot1.id)
        self.assertEqual(game.bot2_id, bot2.id)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.moves, "01478")
        self.assertEqual(game.result_type, "complete")

        actions.report_result(bot1.id, bot2.id, self.build_result(-1))
        actions.report_result(bot2.id, bot1.id, self.build_result(1))
        actions.report_result(bot2.id, bot1.id, self.build_result(0))

        self.assertEqual(bot1.bot1_games.count(), 2)
        self.assertEqual(bot1.bot2_games.count(), 2)

        self.assertEqual(bot1.score, -1)
        self.assertEqual(bot2.score, 1)

    def test_report_result_for_incomplete_game(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        result = self.build_result(1, ResultType.EXCEPTION)
        actions.report_result(bot1.id, bot2.id, result)

        game = models.Game.objects.get()

        self.assertEqual(game.bot1_id, bot1.id)
        self.assertEqual(game.bot2_id, bot2.id)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.moves, "01478")
        self.assertEqual(game.result_type, "exception")
        self.assertEqual(game.traceback, "KeyError ...")

    def test_report_result_when_all_games_played(self):
        bot1, bot2 = [factories.create_bot() for _ in range(2)]

        for _ in range(5):
            factories.report_result(bot1.id, bot2.id, 0)

        actions.report_result(bot1.id, bot2.id, self.build_result(1))

        self.assertEqual(models.Game.objects.count(), 5)
