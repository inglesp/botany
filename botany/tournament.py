from django.conf import settings

from .models import Bot, Game


def unplayed_games_for_bot(bot):
    unplayed_games = {}

    if not bot.is_active:
        return unplayed_games

    for other_bot in Bot.objects.active_bots().exclude(id=bot.id):
        num_bot1_games = bot.bot1_games.filter(bot2=other_bot).count()
        num_bot2_games = bot.bot2_games.filter(bot1=other_bot).count()

        unplayed_games[(bot.id, other_bot.id)] = (
            settings.BOTANY_NUM_ROUNDS - num_bot1_games
        )
        unplayed_games[(other_bot.id, bot.id)] = (
            settings.BOTANY_NUM_ROUNDS - num_bot2_games
        )

    unplayed_games = {ids: count for ids, count in unplayed_games.items() if count > 0}
    return unplayed_games


def all_unplayed_games():
    unplayed_games = {}

    for bot1 in Bot.objects.active_bots():
        for bot2 in Bot.objects.active_bots():
            if bot1 == bot2:
                continue

            unplayed_games[(bot1.id, bot2.id)] = settings.BOTANY_NUM_ROUNDS

    for game in Game.objects.games_between_active_bots():
        unplayed_games[(game.bot1_id, game.bot2_id)] -= 1

    unplayed_games = {ids: count for ids, count in unplayed_games.items() if count > 0}
    return unplayed_games


def calculate_standings():
    sql = """
WITH active_bots AS (
    SELECT * FROM botany_bot
    WHERE is_active
),

annotated_games AS (
    SELECT
        bot1_id AS bot1_id,
        bot2_id AS bot2_id,
        score = 1 AS is_bot1_win,
        score = 0 AS is_bot1_draw,
        score = -1 AS is_bot1_loss,
        score = -1 AS is_bot2_win,
        score = 0 AS is_bot2_draw,
        score = 1 AS is_bot2_loss
    FROM botany_game AS g
    INNER JOIN active_bots AS b1 ON g.bot1_id = b1.id
    INNER JOIN active_bots AS b2 ON g.bot2_id = b2.id
),

bot1_results AS (
    SELECT
        bot1_id AS bot_id,
        COUNT(bot1_id) AS num_played,
        COUNT(is_bot1_win OR NULL) AS num_wins,
        COUNT(is_bot1_draw OR NULL) AS num_draws,
        COUNT(is_bot1_loss OR NULL) AS num_losses
    FROM annotated_games AS g
    GROUP BY bot1_id
),

bot2_results AS (
    SELECT
        bot2_id AS bot_id,
        COUNT(bot2_id) AS num_played,
        COUNT(is_bot2_win OR NULL) AS num_wins,
        COUNT(is_bot2_draw OR NULL) AS num_draws,
        COUNT(is_bot2_loss OR NULL) AS num_losses
    FROM annotated_games AS g
    GROUP BY bot2_id
),

combined_results AS (
    SELECT * FROM bot1_results
    UNION ALL
    SELECT * FROM bot2_results
),

summary_results AS (
    SELECT
        bot_id,
        SUM(num_played) AS num_played,
        SUM(num_wins) AS num_wins,
        SUM(num_draws) AS num_draws,
        SUM(num_losses) AS num_losses,
        SUM(num_wins) - SUM(num_losses) AS score
    FROM combined_results
    GROUP BY bot_id
)

SELECT
    b.*,
    COALESCE(num_played, 0) AS num_played,
    COALESCE(num_wins, 0) AS num_wins,
    COALESCE(num_draws, 0) AS num_draws,
    COALESCE(num_losses, 0) AS num_losses,
    COALESCE(score, 0) AS score
FROM active_bots b
LEFT JOIN summary_results r ON b.id = r.bot_id
ORDER BY score DESC, num_played, num_wins DESC, b.name
    """

    return Bot.objects.raw(sql)
