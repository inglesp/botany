import hypothesis.strategies as st
from hypothesis import assume


@st.composite
def results(draw, num_bots, num_games):
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
