# This is an example game module, also used in botany tests.

TOKENS = ["X", "O"]
EMPTY = "."

LINES_OF_3 = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
]


def new_board():
    return [EMPTY] * 9


def make_move(board, pos, token):
    assert is_valid_move(board, pos)
    board[pos] = token


def available_moves(board):
    return [pos for pos, token in enumerate(board) if token == EMPTY]


def is_valid_move(board, pos):
    return board[pos] == EMPTY


def check_winner(board):
    for line in LINES_OF_3:
        if board[line[0]] == EMPTY:
            continue

        if board[line[0]] == board[line[1]] == board[line[2]]:
            return board[line[0]]

    return None


def render_html(board):
    return """
      <div class="noughtsandcrosses-grid">
        <table>
          <tr>
            <td class="bordered-right bordered-bottom">{}</td>
            <td class="bordered-right bordered-bottom">{}</td>
            <td class="bordered-bottom">{}</td>
          </tr>
          <tr>
            <td class="bordered-right bordered-bottom">{}</td>
            <td class="bordered-right bordered-bottom">{}</td>
            <td class="bordered-bottom">{}</td>
          </tr>
          <tr>
            <td class="bordered-right bordered-left">{}</td>
            <td class="bordered-right">{}</td>
            <td>{}</td>
          </tr>
        </table>
      </div>
    """.format(
        *board
    )


html_styles = """
.noughtsandcrosses-grid table {
  table-layout: fixed;
  font-size: 120px;
}

.noughtsandcrosses-grid td {
  width: 180px;
  height: 180px;
  text-align: center;
  vertical-align: center;
}

.noughtsandcrosses-grid td.bordered-bottom {
  border-bottom: 2px solid;
}

.noughtsandcrosses-grid td.bordered-right {
  border-right: 2px solid;
}
"""


def render_text(board):
    s = """
{} | {} | {}
--+---+---
{} | {} | {}
--+---+---
{} | {} | {}
"""
    return s.format(*board)
