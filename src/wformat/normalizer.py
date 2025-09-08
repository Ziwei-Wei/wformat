import re
from pathlib import Path
import traceback

INTEGER_LITERAL_PATTERN = re.compile(
    r"\b((0[bB]([01][01']*[01]|[01]+))|(0[xX]([\da-fA-F][\da-fA-F']*[\da-fA-F]|[\da-fA-F]+))|(0([0-7][0-7']*[0-7]|[0-7]+))|([1-9](\d[\d']*\d|\d*)))([uU]?[lL]{0,2}|[lL]{0,2}[uU]?)?\b"
)
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_]\w*")
RETURN_TYPE_PATTERN = re.compile(
    r"^\s*(inline|static|constexpr|virtual|friend|typedef|using|void|[A-Za-z_][A-Za-z0-9_]*)"
)
DISALLOWED_CHARS_PATTERN = re.compile(r".*[\;\(\)\{\}\\].*")
LEADING_SPACES_PATTERN = re.compile(r"^\s*")


def normalize_integer_literal(file_path: Path, upper_case: bool = True) -> None:
    try:
        with open(file_path, "r+", encoding="utf-8") as file:
            code = file.read()
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(normalize_integer_literal_in_memory(code, upper_case))
    except Exception:
        print(traceback.format_exc())


def normalize_integer_literal_in_memory(data: str, upper_case: bool = True) -> str:
    def replace(match: re.Match[str]):
        update = match.group(0)
        update = update.upper() if upper_case else update.lower()
        if len(update) > 1 and update[0] == "0":
            update = update[0] + update[1].lower() + update[2:]
        if data[match.start() - 1] == "&":
            update = " " + update
        return update

    return INTEGER_LITERAL_PATTERN.sub(repl=replace, string=data)


def normalize_single_param_func_call(src: str) -> str:
    """
    Collapse only the *inside* of simple single-parameter calls.
    Only collapse when there is exactly one top-level argument with no parentheses.
    """

    out = []
    i, n = 0, len(src)

    while i < n:
        m = IDENTIFIER_PATTERN.match(src, i)
        if not m:
            out.append(src[i])
            i += 1
            continue

        # name [whitespace] '(' ...
        name_start = i
        j = m.end()
        while j < n and src[j].isspace():
            j += 1
        if j >= n or src[j] != "(":
            # Not a call/def; copy through what we consumed
            out.append(src[i:j])
            i = j
            continue

        # Find matching ')', track commas at top level
        depth, k = 0, j
        comma_at_top = False
        while k < n:
            ch = src[k]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    k += 1  # include ')'
                    break
            elif ch == "," and depth == 1:
                comma_at_top = True
            k += 1

        if depth != 0:
            # Unbalanced: fail safe
            out.append(src[i])
            i += 1
            continue

        # Inside content (between the outer parens)
        inside_orig = src[j + 1 : k - 1]

        # Recurse inside first
        inside_proc = normalize_single_param_func_call(inside_orig)

        # Simple = exactly one top-level arg and it contains no parentheses
        is_single_param = not comma_at_top
        is_simple_arg = "(" not in inside_proc and ")" not in inside_proc

        # Determine whether this paren group belongs to a function declaration/definition.
        # We look ahead after the closing ')' skipping whitespace and comments.
        p = k
        def _skip_ws_and_comments(idx: int) -> int:
            while idx < n:
                # skip whitespace
                while idx < n and src[idx].isspace():
                    idx += 1
                # line comment
                if src.startswith("//", idx):
                    idx_end = src.find("\n", idx + 2)
                    if idx_end == -1:
                        return n
                    idx = idx_end + 1
                    continue
                # block comment
                if src.startswith("/*", idx):
                    endc = src.find("*/", idx + 2)
                    if endc == -1:
                        return n
                    idx = endc + 2
                    continue
                break
            return idx

        p = _skip_ws_and_comments(p)
        next_ch = src[p] if p < n else ""
        is_func_decl_or_def = next_ch == ";" or next_ch == "{"

        if is_single_param and is_simple_arg and not is_func_decl_or_def:
            # Preserve everything up to and including '(' exactly as in the source,
            # only collapse whitespace *inside* the parens.
            prefix_including_paren = src[i : j + 1]  # name + original whitespace + '('
            arg = re.sub(r"\s+", " ", inside_proc).strip()
            out.append(prefix_including_paren)
            out.append(arg)
            out.append(")")
        else:
            # Keep outer layout; use processed interior
            out.append(src[i : j + 1])  # original up to '('
            out.append(inside_proc)
            out.append(")")

        i = k  # continue after ')'

    return "".join(out)


def normalize_function_indent(src: str) -> str:
    """
    Normalize indentation of function definitions/declarations:
    - Keep return type / specifiers at their line's indent.
    - Place the function name at the *same indent*, not indented further.
    """
    lines = src.splitlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect a "return type/specifier" line (heuristic: ends without '(' and no ';')
        if RETURN_TYPE_PATTERN.match(line) and not DISALLOWED_CHARS_PATTERN.match(line):
            # Look ahead: next line that contains a '(' → likely the function name
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if "(" in next_line:
                    # indent level of the first line
                    base_indent = LEADING_SPACES_PATTERN.match(line).group(0)
                    # strip leading spaces from next_line
                    stripped_next = next_line.lstrip()
                    out_lines.append(line)
                    out_lines.append(base_indent + stripped_next)
                    i += 2
                    continue

        # Default: just copy
        out_lines.append(line)
        i += 1

    return "\n".join(out_lines)
