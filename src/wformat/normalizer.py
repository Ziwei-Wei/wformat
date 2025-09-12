import re
from pathlib import Path
import traceback
from typing import Any, Pattern, Match
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_cpp as ts_cpp

# try https://tree-sitter.github.io/tree-sitter/7-playground.html

_CPP_LANGUAGE: Language = Language(ts_cpp.language())
_PARSER: Parser = Parser(_CPP_LANGUAGE)
_QUERY: Query = Query(
    _CPP_LANGUAGE,
    """
    (call_expression) @call
    (function_definition) @func
    (declaration) @func
    (field_declaration) @func
    """.strip(),
)

_INTEGER_LITERAL_PATTERN: Pattern[str] = re.compile(
    r"\b((0[bB]([01][01']*[01]|[01]+))|(0[xX]([\da-fA-F][\da-fA-F']*[\da-fA-F]|[\da-fA-F]+))|(0([0-7][0-7']*[0-7]|[0-7]+))|([1-9](\d[\d']*\d|\d*)))([uU]?[lL]{0,2}|[lL]{0,2}[uU]?)?\b"
)

# (start_byte, end_byte, replacement_bytes)
Edit = tuple[int, int, bytes]


def normalize_integer_literal(file_path: Path, upper_case: bool = True) -> None:
    try:
        with open(file_path, "r+", encoding="utf-8") as file:
            code = file.read()
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(normalize_integer_literal_in_memory(code, upper_case))
    except Exception:
        print(traceback.format_exc())


def normalize_integer_literal_in_memory(data: str, upper_case: bool = True) -> str:
    def replace(match: Match[str]) -> str:
        update = match.group(0)
        update = update.upper() if upper_case else update.lower()
        if len(update) > 1 and update[0] == "0":
            update = update[0] + update[1].lower() + update[2:]
        if data[match.start() - 1] == "&":
            update = " " + update
        return update

    return _INTEGER_LITERAL_PATTERN.sub(repl=replace, string=data)


def fix_with_tree_sitter(code: str) -> str:
    if not code:
        return code

    src: bytes = code.encode("utf-8")
    tree = _PARSER.parse(src)

    edits: list[Edit] = []
    edits += fix_single_arg_func_calls(src, tree)
    edits += fix_func_indent(src, tree)

    edits.sort(key=lambda e: e[0], reverse=True)
    for start, end, rep in edits:
        src = src[:start] + rep + src[end:]
    return src.decode("utf-8")


def fix_func_indent(src: bytes, tree: Any) -> list[Edit]:
    cursor: QueryCursor = QueryCursor(_QUERY)
    captures: Any = cursor.captures(
        tree.root_node
    )  # library-specific dynamic structure

    call_nodes: list[Any] = captures.get("func", [])  # type: ignore[index]
    iterable: list[tuple[Any, str]] = [(n, "func") for n in call_nodes]

    edits: list[Edit] = []
    for node, cap_name in iterable:

        if cap_name != "func":
            continue

        return_type: Any = node.child_by_field_name("type")
        declarator: Any = node.child_by_field_name("declarator")

        if return_type is None or declarator is None:
            continue

        return_type_row: int = return_type.start_point[0]
        return_type_col: int = return_type.start_point[1]
        declarator_row: int = declarator.start_point[0]
        declarator_col: int = declarator.start_point[1]

        dist: int = declarator_col - return_type_col

        if return_type_row < declarator_row and dist > 0:
            edits.append(
                (
                    declarator.start_byte - dist,
                    declarator.end_byte,
                    src[declarator.start_byte : declarator.end_byte],
                )
            )
    return edits


def fix_single_arg_func_calls(src: bytes, tree: Any) -> list[Edit]:
    cursor: QueryCursor = QueryCursor(_QUERY)
    captures: Any = cursor.captures(tree.root_node)

    call_nodes: list[Any] = captures.get("call", [])  # type: ignore[index]
    iterable: list[tuple[Any, str]] = [(n, "call") for n in call_nodes]

    edits: list[Edit] = []
    for node, cap_name in iterable:
        if cap_name != "call":
            continue
        func: Any = node.child_by_field_name("function")
        args: Any = node.child_by_field_name("arguments")
        if func is None or args is None:
            continue
        flat_args: list[Any] = []
        has_comment: bool = False
        for c in args.named_children:
            if c.type == "comment":
                has_comment = True
                break
            if c.type == "argument" and c.named_children:
                flat_args.append(c.named_children[0])
            else:
                flat_args.append(c)
        if has_comment or len(flat_args) != 1:
            continue

        if flat_args[0].type == "call_expression":
            continue

        args_text: str = src[args.start_byte : args.end_byte].decode("utf-8")
        if not (args_text.startswith("(") and args_text.endswith(")")):
            continue

        new_args_text: str = f"({args_text[1:-1].strip()})"
        if new_args_text != args_text:
            edits.append(
                (args.start_byte, args.end_byte, new_args_text.encode("utf-8"))
            )

    return edits
