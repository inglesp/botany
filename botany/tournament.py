from .models import Bot


def calculate_standings():
    sql = """
WITH active_bots AS (
    SELECT * FROM botany_bot
    WHERE is_active = 1
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
        SUM(is_bot1_win) AS num_wins,
        SUM(is_bot1_draw) AS num_draws,
        SUM(is_bot1_loss) AS num_losses
    FROM annotated_games AS g
    GROUP BY bot1_id
),

bot2_results AS (
    SELECT
        bot2_id AS bot_id,
        COUNT(bot2_id) AS num_played,
        SUM(is_bot2_win) AS num_wins,
        SUM(is_bot2_draw) AS num_draws,
        SUM(is_bot2_loss) AS num_losses
    FROM annotated_games AS g
    GROUP BY bot2_id
),

results AS (
    SELECT * FROM bot1_results
    UNION ALL
    SELECT * FROM bot2_results
)

SELECT
    b.*,
    COALESCE(SUM(num_played), 0) AS num_played,
    COALESCE(SUM(num_wins), 0) AS num_wins,
    COALESCE(SUM(num_draws), 0) AS num_draws,
    COALESCE(SUM(num_losses), 0) AS num_losses,
    COALESCE(SUM(num_wins) - SUM(num_losses), 0) AS score
FROM active_bots b
LEFT JOIN results r ON b.id = r.bot_id
GROUP BY b.id
ORDER BY score DESC, num_played, num_wins DESC, b.name
    """

    return Bot.objects.raw(sql)
