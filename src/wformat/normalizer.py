import re
from pathlib import Path
import traceback
from typing import Any, Pattern, Match
from tree_sitter import Language, Parser, Query, QueryCursor, Node
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
    captures: dict[str, list[Node]] = cursor.captures(tree.root_node)
    func_nodes: list[Node] = captures.get("func", [])
    edits: list[Edit] = []
    for node in func_nodes:
        type: Node | None = node.child_by_field_name("type")
        declarator: Node | None = node.child_by_field_name("declarator")

        if type and declarator and declarator.grammar_name == "function_declarator":
            return_type_row: int = type.start_point[0]
            return_type_col: int = type.start_point[1]
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
    captures: dict[str, list[Node]] = cursor.captures(tree.root_node)
    call_nodes: list[Node] = captures.get("call", [])
    edits: list[Edit] = []
    for node in call_nodes:
        function: Node | None = node.child_by_field_name("function")
        arguments: Node | None = node.child_by_field_name("arguments")
        if function and arguments and len(arguments.named_children) == 1:

            first_grammar_name = arguments.named_children[0].grammar_name
            if (
                first_grammar_name == "lambda_expression"
                or first_grammar_name == "call_expression"
            ):
                continue

            args_text: str = src[arguments.start_byte : arguments.end_byte].decode(
                "utf-8"
            )
            if not (args_text.startswith("(") and args_text.endswith(")")):
                continue

            new_args_text: str = f"({args_text[1:-1].strip()})"
            if new_args_text != args_text:
                edits.append(
                    (
                        arguments.start_byte,
                        arguments.end_byte,
                        new_args_text.encode("utf-8"),
                    )
                )

    return edits
