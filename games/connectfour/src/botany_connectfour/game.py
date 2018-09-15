N = 4
NROWS = 6
NCOLS = 7

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


EMPTY = "."
TOKENS = ["X", "O"]


def new_board():
    return [[EMPTY for _ in range(NROWS)] for _ in range(NCOLS)]


def make_move(board, col, token):
    assert is_valid_move(board, col)
    for row in range(NROWS):
        if board[col][row] == EMPTY:
            board[col][row] = token
            break


def available_moves(board):
    return [col for col in range(NCOLS) if is_valid_move(board, col)]


def is_valid_move(board, col):
    return board[col][-1] == EMPTY


def check_winner(board):
    for line in LINES_OF_4:
        col0, row0 = line[0]
        token0 = board[col0][row0]

        if token0 == EMPTY:
            continue

        if all(board[col][row] == token0 for col, row in line[1:]):
            return token0

    return None


def render_html(board):
    html = """
      <div class="connectfour-grid">
        <table>
    """

    for row in range(NROWS)[::-1]:
        html += """
            <tr>
        """

        for col in range(NCOLS):
            html += f"<td>{board[col][row]}</td>"

        html += """
            </tr>
        """

    html += """
        </table>
    </div>
    """

    return html


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


def render_text(board):
    lines = []
    for row in range(NROWS)[::-1]:
        lines.append(" ".join(board[col][row] for col in range(NCOLS)))
    return "\n" + "\n".join(lines) + "\n"
