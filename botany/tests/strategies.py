import hypothesis.strategies as st
from hypothesis import assume


@st.composite
def results(draw, num_bots, num_games):
    """Strategy to generate results of tournament.

    The tournament is between num_bots bots, and num_games games have been
    playd so far.

    Returns list (of length num_games) of tuples (bot1_ix, bot2_ix, score),
    where bot1_ix and bot2_ix are indexes into a list (of length num_bots) of
    bots and score is in [-1, 0, 1].  Each tuple represents the results of a
    single game.

    It is up to the test that uses this strategy to filter out any results that
    don't make sense in the context of the test.  For instance, if the test has
    a list of bots where some bots belong to the same user, the test might
    ignore any results where bot1.user == bot2.user.
    """
    bot1_ixs = draw(
        st.lists(
            st.integers(min_value=0, max_value=num_bots - 1),
            min_size=num_games,
            max_size=num_games,
        )
    )
    bot2_ixs = draw(
        st.lists(
            st.integers(min_value=0, max_value=num_bots - 1),
            min_size=num_games,
            max_size=num_games,
        )
    )
    scores = draw(
        st.lists(
            st.integers(min_value=-1, max_value=1),
            min_size=num_games,
            max_size=num_games,
        )
    )

    assume(bot1_ixs != bot2_ixs)

    return list(zip(bot1_ixs, bot2_ixs, scores))
