#!/usr/bin/env python3
"""
Генератор таблицы подсимволов {СИМВОЛ_подсимвол} по имени C#-типа.

Разбирает метод TryResolveSymbol прямо в
.Decompiled/Verse/GrammarResolverSimple.cs, поэтому результат не может
"отстать" от кода игры, в отличие от таблицы, переписанной вручную.

Использование:
  python tools/subsymbols.py Pawn
  python tools/subsymbols.py            # список всех найденных типов
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECOMPILED_FILE = REPO_ROOT / ".Decompiled" / "Verse" / "GrammarResolverSimple.cs"

CASE_RE = re.compile(r'case\s+"([^"]*)"\s*:')
SUBSYMBOL_EQ_RE = re.compile(r'subSymbol\s*==\s*"([^"]*)"')
SUBSYMBOL_EMPTY_RE = re.compile(
    r'subSymbol\.Length\s*==\s*0|subSymbol\.NullOrEmpty\(\)|subSymbol\.Length\s*!=\s*0'
)
IS_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\s+is\s+([A-Za-z_][A-Za-z0-9_.]*)')


def find_matching_paren(text: str, open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced parens")


def find_matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced braces")


def mask_nested_type_blocks(text: str) -> str:
    """Blank out nested `if (X is Y ...) { ... }` blocks so an outer type's
    subsymbols aren't polluted by a more specific nested type's own switch
    (e.g. PawnKindDef refining Def)."""
    result = list(text)
    pos = 0
    if_re = re.compile(r'if\s*\(')
    while True:
        m = if_re.search(text, pos)
        if not m:
            break
        open_paren = m.end() - 1
        close_paren = find_matching_paren(text, open_paren)
        cond = text[open_paren + 1:close_paren]
        p = close_paren + 1
        while p < len(text) and text[p] in ' \t\r\n':
            p += 1
        if p < len(text) and text[p] == '{' and IS_RE.search(cond):
            close_brace = find_matching_brace(text, p)
            for i in range(m.start(), close_brace + 1):
                result[i] = ' '
            pos = close_brace + 1
        else:
            pos = close_paren + 1
    return ''.join(result)


def find_is_blocks(text: str) -> list[tuple[list[str], str]]:
    """Recursively yield (type_names, own_block_text) for every top-level and
    nested `if (VAR is TYPE ...) { ... }` inside `text`. Several types joined
    by `||` in one condition (e.g. `obj is int || obj is long`) share one
    entry, since they share the same handling block."""
    results = []
    pos = 0
    if_re = re.compile(r'if\s*\(')
    while True:
        m = if_re.search(text, pos)
        if not m:
            break
        open_paren = m.end() - 1
        close_paren = find_matching_paren(text, open_paren)
        cond = text[open_paren + 1:close_paren]
        p = close_paren + 1
        while p < len(text) and text[p] in ' \t\r\n':
            p += 1
        types = IS_RE.findall(cond)
        if p < len(text) and text[p] == '{' and types:
            close_brace = find_matching_brace(text, p)
            block = text[p + 1:close_brace]
            results.append((types, mask_nested_type_blocks(block)))
            results.extend(find_is_blocks(block))
            pos = close_brace + 1
        else:
            pos = close_paren + 1
    return results


def extract_subsymbols(block_text: str) -> dict[str, bool]:
    """Return {subsymbol_name: takes_extra_args_via_question_mark}."""
    result: dict[str, bool] = {}
    case_matches = list(CASE_RE.finditer(block_text))
    for idx, m in enumerate(case_matches):
        start = m.end()
        end = case_matches[idx + 1].start() if idx + 1 < len(case_matches) else len(block_text)
        default_m = re.search(r'\bdefault\s*:', block_text[start:end])
        body_end = start + default_m.start() if default_m else end
        body = block_text[start:body_end]
        # EnsureNoArgs(subSymbol, symbolArgs, ...) mentions symbolArgs to assert
        # it's empty — that's the opposite signal from actually consuming it.
        takes_args = 'EnsureNoArgs' not in body and 'symbolArgs' in body
        result[m.group(1)] = result.get(m.group(1), False) or takes_args
    for m in SUBSYMBOL_EQ_RE.finditer(block_text):
        result.setdefault(m.group(1), False)
    if SUBSYMBOL_EMPTY_RE.search(block_text):
        result.setdefault('', False)
    return result


def build_symbol_table(cs_text: str) -> list[dict]:
    method_m = re.search(r'private static bool TryResolveSymbol\s*\([^)]*\)\s*\{', cs_text)
    if not method_m:
        raise RuntimeError(
            "Не найден метод TryResolveSymbol — формат GrammarResolverSimple.cs "
            "мог измениться в новой версии игры."
        )
    body_start = method_m.end() - 1
    body_end = find_matching_brace(cs_text, body_start)
    method_body = cs_text[body_start + 1:body_end]

    table = []
    for types, block in find_is_blocks(method_body):
        subsymbols = extract_subsymbols(block)
        if subsymbols:
            table.append({"types": types, "subsymbols": subsymbols})
    return table


def format_table(records: list[dict]) -> str:
    lines = []
    for rec in records:
        lines.append(f"## {' / '.join(rec['types'])}")
        lines.append("")
        for name, takes_args in sorted(rec["subsymbols"].items(), key=lambda kv: (kv[0] != "", kv[0])):
            label = '""' if name == "" else f"`{name}`"
            suffix = " (принимает аргументы через `?арг1:арг2:...`)" if takes_args else ""
            lines.append(f"- {label}{suffix}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("type", nargs="?", help="Имя C#-типа (Pawn, Thing, Faction, ...). Без аргумента — список всех типов.")
    args = parser.parse_args()

    if not DECOMPILED_FILE.exists():
        print(
            f"Не найден файл {DECOMPILED_FILE}.\n"
            "Похоже, .Decompiled не подключён локально. Настройте его через "
            "script/setup.ps1 (требуется установленная локально через Steam копия "
            "RimWorld) и повторите попытку.",
            file=sys.stderr,
        )
        sys.exit(1)

    cs_text = DECOMPILED_FILE.read_text(encoding="utf-8-sig")
    try:
        records = build_symbol_table(cs_text)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if not records:
        print("Не удалось разобрать TryResolveSymbol — ни одного типа не найдено.", file=sys.stderr)
        sys.exit(1)

    if args.type:
        matched = [r for r in records if any(t.lower() == args.type.lower() for t in r["types"])]
        if not matched:
            available = sorted({t for r in records for t in r["types"]})
            print(f"Тип '{args.type}' не найден. Доступные типы: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)
        print(format_table(matched))
    else:
        print(format_table(records))


if __name__ == "__main__":
    main()
