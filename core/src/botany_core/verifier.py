import ast


class InvalidBotCode(Exception):
    pass


def verify_bot_code(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        msg = "\n".join(
            [
                f"Bot code contains a SyntaxError on line {e.lineno}",
                "",
                "  " + e.text.rstrip(),
                " " * e.offset + "^",
                f"{type(e).__name__}: {e.msg}",
            ]
        )
        raise InvalidBotCode(msg)

    found_get_next_move = False

    for stmt in tree.body:
        if type(stmt) not in [ast.Import, ast.ImportFrom, ast.FunctionDef]:
            msg = f"Found something that's not an import or a function definition on line {stmt.lineno}"
            raise InvalidBotCode(msg)

        if isinstance(stmt, ast.FunctionDef):
            if stmt.name == "get_next_move":
                found_get_next_move = True

                args = stmt.args
                arg_names = [arg.arg for arg in args.args + args.kwonlyargs]

                if "board" not in arg_names and "move_list" not in arg_names:
                    msg = "get_next_move() must have either a parameter called `board` or a parameter called `move_list`, or both"
                    raise InvalidBotCode(msg)

                for arg_name in arg_names:
                    if arg_name not in ["board", "move_list", "token", "state"]:
                        msg = "get_next_move() may only have parameters called `board`, `move_list`, `token`, or `state`"
                        raise InvalidBotCode(msg)

    if not found_get_next_move:
        msg = "Bot code does not define a function called get_next_move"
        raise InvalidBotCode(msg)
