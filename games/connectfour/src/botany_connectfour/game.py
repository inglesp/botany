# This module contains code used by Botany to play Connect Four.
#
# A Connect Four board is a grid 42 cells, made up of 7 columns and 6 rows.
#
# The functions in this module uses a list of list to represent a board.  The
# outer list has 7 elements (one for each column) while each inner list has six
# elements (one for each row).  The first element in an inner list represents
# the bottom cell in a column, and the last represents the top cell.


# Some parameters
N = 4
NROWS = 6
NCOLS = 7


# A list of lists, where each list contains four (col, row) pairs representing
# each of the possible lines of four on a board.
LINES_OF_4 = []

for row in range(NROWS):
    for col in range(NCOLS - N + 1):
        LINES_OF_4.append([(col + ix, row) for ix in range(N)])

for col in range(NCOLS):
    for row in range(NROWS - N + 1):
        LINES_OF_4.append([(col, row + ix) for ix in range(N)])

for row in range(NROWS - N + 1):
    for col in range(NCOLS - N + 1):
        LINES_OF_4.append([(col + ix, row + ix) for ix in range(N)])
        LINES_OF_4.append([(col + ix, row + N - 1 - ix) for ix in range(N)])


# Value representing an empty cell
EMPTY = "."

# Tokens for bot1 and bot2
TOKENS = ["X", "O"]


def new_board():
    """Return a new board"""
    return [[EMPTY for _ in range(NROWS)] for _ in range(NCOLS)]


def make_move(board, col, token):
    """Update `board`, by dropping `token` in `col`"""
    assert is_valid_move(board, col)
    for row in range(NROWS):
        if board[col][row] == EMPTY:
            board[col][row] = token
            break


def available_moves(board):
    """Return list of columns which """
    return [col for col in range(NCOLS) if is_valid_move(board, col)]


def is_valid_move(board, col):
    """Return boolean indicating whether `col` is a valid move in `board`."""
    return board[col][-1] == EMPTY


def check_winner(board):
    """Return token (either "X" or "O") if there are four tokens in a row, or
    None if there are no rows of four."""
    for line in LINES_OF_4:
        col0, row0 = line[0]
        token0 = board[col0][row0]

        if token0 == EMPTY:
            continue

        if all(board[col][row] == token0 for col, row in line[1:]):
            return token0

    return None


def render_text(board):
    """Return string suitable for printing board in terminal."""
    lines = []
    for row in range(NROWS)[::-1]:
        lines.append(" ".join(board[col][row] for col in range(NCOLS)))
    return "\n" + "\n".join(lines) + "\n"


def render_html(board):
    """Return string suitable for displaying board in browser."""
    html = """
      <div class="connectfour-grid">
        <table>
    """

    for row in range(NROWS)[::-1]:
        html += """
            <tr>
        """

        for col in range(NCOLS):
            if col in available_moves(board) and not check_winner(board):
                html += f'<td class="connectfour-col active" data-connectfourcol="{col}">{board[col][row]}</td>'
            else:
                html += f'<td class="connectfour-col">{board[col][row]}</td>'

        html += """
            </tr>
        """

    html += """
        </table>
    </div>
    """

    return html


# Used to style games on the website.
html_styles = """
.connectfour-grid table {
  table-layout: fixed;
  font-size: 60px;
}

.connectfour-grid td {
  width: 60px;
  height: 60px;
  text-align: center;
  vertical-align: center;
}
"""
