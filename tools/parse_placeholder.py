#!/usr/bin/env python3
"""
Детерминированный разбор синтаксиса {...}-конструкций (символ/подсимвол,
функция, экранирование, вложенность) в строке Keyed/DefInjected — независимо
от того, что именно означает конкретный N/ИМЯ или подсимвол в игре. Полное
описание правил разбора (человеческим языком, с примерами) —
docs/agents/placeholder-syntax.md; этот скрипт реализует ровно те же правила
механически, вместо того чтобы полагаться на то, что языковая модель без
инструментов правильно проследит вложенность и разделители вручную.

Это ручной порт синтаксического разбора из метода TryResolveInner
(.Decompiled/Verse/GrammarResolverSimple.cs) — сам алгоритм разбора фигурных
скобок стабилен между версиями игры (в отличие от списка подсимволов на
конкретный C#-тип, для этого используйте tools/subsymbols.py), поэтому скрипт
не читает .Decompiled и не зависит от того, настроен ли юнкшен.

Скрипт НЕ подставляет реальные игровые значения — это не то же самое, что
"что именно окажется на месте {0}" (см. docs/agents/howto-resolve-placeholder.md),
а только механическая структура самой конструкции: какой это вид (символ,
функция, экранирование), какой N/ИМЯ, какой подсимвол, какие аргументы — в
том числе вложенные конструкции внутри аргументов, разобранные рекурсивно.

Использование:
  python tools/parse_placeholder.py "{0_numCase?год:года:лет}"
  python tools/parse_placeholder.py --json "{replace: {lookup: {1}; Case; 3}; \"область\"-\"\"}"
  python tools/parse_placeholder.py < строка.txt     # без аргумента — читает из stdin
  python tools/parse_placeholder.py --self-test      # проверка на реальных примерах из репозитория

Можно передавать как один плейсхолдер (`{...}`), так и всю строку целиком
(с обычным текстом до/после/между плейсхолдерами) — разбираются все
конструкции по порядку.

Известное упрощение: если вложенный "{...}" использован там, где игра его не
поддерживает (не после "?" и не после "имяФункции:"), скрипт помечает всю
конструкцию как ошибку, а не воспроизводит запутанное поведение восстановления
разбора игры после такой ошибки (см. docs/agents/placeholder-syntax.md,
раздел "Типичные ошибки разбора").
"""
import argparse
import json
import re
import sys

_INDEX_RE = re.compile(r"-?\d+")


def find_construct(text: str, open_pos: int):
    """Разобрать одну конструкцию `{...}`, начинающуюся в text[open_pos] == '{'.
    Возвращает (node, next_pos), где next_pos — позиция сразу после
    закрывающей '}' этой конструкции (как charIndex в TryResolveInner после
    обработки одной конструкции)."""
    n = len(text)
    j = open_pos + 1
    has_inner = j < n and text[j] == "{"

    if has_inner:
        close = text.find("}", j)
        if close == -1:
            return _error(text[open_pos:], "не найдена закрывающая '}'"), n
        return {
            "kind": "escape",
            "raw": text[open_pos:close + 1],
            "literal": text[j:close],
        }, close + 1

    # Попытка распознать "имяФункции:" сразу после '{' (без пробела перед ':').
    k = j
    prev_nonspace = False
    name_chars = []
    colon_found = False
    while k < n:
        ch = text[k]
        if ch in "{}?" or (ch == " " and prev_nonspace):
            break
        if ch != " ":
            prev_nonspace = True
        if ch == ":":
            colon_found = True
            break
        name_chars.append(ch)
        k += 1

    if colon_found:
        return _parse_function(text, open_pos, "".join(name_chars), k + 1, n)
    return _parse_symbol(text, open_pos, j, n)


def _error(raw: str, message: str) -> dict:
    return {"kind": "error", "raw": raw, "message": message}


def _scan_body(text: str, start: int, n: int):
    """Читать содержимое от `start` до первой не вложенной '}'. Вложенные
    `{...}` целиком поглощаются через find_construct (рекурсивно), поэтому их
    собственные ';'/':'/'_'/'?' никогда не попадают в текущий уровень.
    Возвращает (tokens, close_pos); close_pos == -1, если закрывающая '}' не
    найдена до конца строки. tokens — список из строк и dict-узлов вперемешку,
    в порядке появления."""
    tokens = []
    literal = []
    i = start
    while i < n:
        c = text[i]
        if c == "}":
            if literal:
                tokens.append("".join(literal))
            return tokens, i
        if c == "{":
            if literal:
                tokens.append("".join(literal))
                literal = []
            node, i = find_construct(text, i)
            tokens.append(node)
            continue
        literal.append(c)
        i += 1
    if literal:
        tokens.append("".join(literal))
    return tokens, -1


def _split_tokens(tokens, delimiter: str):
    """Разбить список токенов (строки/dict вперемешку) по `delimiter`, но
    только внутри строковых токенов — dict-токены (уже разобранные вложенные
    конструкции) атомарны и никогда не делятся, даже если внутри них есть
    символ-разделитель этого уровня."""
    groups = [[]]
    for tok in tokens:
        if isinstance(tok, str):
            pieces = tok.split(delimiter)
            for idx, piece in enumerate(pieces):
                if idx > 0:
                    groups.append([])
                if piece != "":
                    groups[-1].append(piece)
        else:
            groups[-1].append(tok)
    return groups


def _simplify_group(group):
    """Обрезать пробелы по краям группы (аналог трима внутри GetArg) и
    свернуть группу из одного элемента в сам этот элемент (строку или узел)."""
    group = list(group)
    if group and isinstance(group[0], str):
        group[0] = group[0].lstrip()
        if group[0] == "":
            group = group[1:]
    if group and isinstance(group[-1], str):
        group[-1] = group[-1].rstrip()
        if group[-1] == "":
            group = group[:-1]
    if not group:
        return ""
    if len(group) == 1:
        return group[0]
    return group  # смешанный аргумент (текст вперемешку с вложенными узлами) — на практике не встречается


def _parse_function(text: str, open_pos: int, name: str, content_start: int, n: int):
    tokens, close = _scan_body(text, content_start, n)
    if close == -1:
        return _error(text[open_pos:], "не найдена закрывающая '}' у функции"), n
    args = [_simplify_group(g) for g in _split_tokens(tokens, ";")]
    return {
        "kind": "function",
        "raw": text[open_pos:close + 1],
        "name": name,
        "args": args,
    }, close + 1


def _parse_symbol(text: str, open_pos: int, start: int, n: int):
    i = start
    object_chars = []
    subsymbol_chars = []
    args_tokens = []
    args_literal = []
    underscore_found = False
    question_found = False
    nested_error_pos = None

    while i < n:
        c = text[i]
        if c == "}":
            break
        if c == "{":
            if question_found:
                if args_literal:
                    args_tokens.append("".join(args_literal))
                    args_literal = []
                node, i = find_construct(text, i)
                args_tokens.append(node)
                continue
            if nested_error_pos is None:
                nested_error_pos = i
            i += 1
            continue
        if c == "_" and not underscore_found:
            underscore_found = True
        elif c == "?" and not question_found:
            question_found = True
        elif question_found:
            args_literal.append(c)
        elif underscore_found:
            subsymbol_chars.append(c)
        else:
            object_chars.append(c)
        i += 1

    if args_literal:
        args_tokens.append("".join(args_literal))
    if i >= n or text[i] != "}":
        return _error(text[open_pos:], "не найдена закрывающая '}'"), n

    close = i
    raw = text[open_pos:close + 1]
    if nested_error_pos is not None:
        return _error(
            raw,
            "вложенный '{...}' использован не после '?' и не после 'имяФункции:' — "
            "так не поддерживается игрой (см. docs/agents/placeholder-syntax.md, "
            "раздел «Вложенность»)",
        ), close + 1

    object_label = "".join(object_chars)
    subsymbol = None
    if underscore_found:
        subsymbol = "".join(subsymbol_chars)
        if question_found:
            # Игра обрезает подсимвол справа от пробелов только когда есть '?'
            # (см. GrammarResolverSimple.TryResolveInner) — иначе "{0_gender ?...}"
            # искал бы подсимвол "gender " (с пробелом) и не находил его.
            subsymbol = subsymbol.rstrip(" ")

    args = [_simplify_group(g) for g in _split_tokens(args_tokens, ":")] if question_found else []
    is_index = bool(_INDEX_RE.fullmatch(object_label))

    return {
        "kind": "symbol",
        "raw": raw,
        "object": object_label,
        "object_kind": "index" if is_index else "name",
        "subsymbol": subsymbol,
        "args": args,
    }, close + 1


def parse_text(text: str):
    """Разобрать всю строку (обычный текст вперемешку с `{...}`-конструкциями)
    в список узлов верхнего уровня: обычные строки и dict-конструкции, по
    порядку появления."""
    nodes = []
    literal = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "{":
            if literal:
                nodes.append("".join(literal))
                literal = []
            node, i = find_construct(text, i)
            nodes.append(node)
            continue
        literal.append(c)
        i += 1
    if literal:
        nodes.append("".join(literal))
    return nodes


def _render_arg(arg, indent: str, lines: list):
    if isinstance(arg, str):
        lines.append(f"{indent}{arg!r}")
    elif isinstance(arg, list):
        lines.append(f"{indent}(смешанный аргумент из текста и вложенных конструкций)")
        for part in arg:
            _render_arg(part, indent + "  ", lines)
    else:
        _render_node(arg, indent, lines)


def _render_node(node, indent: str, lines: list):
    kind = node["kind"]
    if kind == "error":
        lines.append(f'{indent}ОШИБКА: {node["message"]}  (текст: {node["raw"]!r})')
        return
    if kind == "escape":
        lines.append(
            f'{indent}ЭКРАНИРОВАНИЕ -> буквальный текст: "{node["literal"]}"  (исходно: {node["raw"]})'
        )
        return
    if kind == "symbol":
        head = f'{indent}СИМВОЛ {node["object"]!r} ({node["object_kind"]})'
        if node["subsymbol"] is not None:
            head += f', подсимвол={node["subsymbol"]!r}'
        lines.append(head)
        for idx, arg in enumerate(node["args"], 1):
            lines.append(f"{indent}  аргумент {idx}:")
            _render_arg(arg, indent + "    ", lines)
        return
    if kind == "function":
        lines.append(f'{indent}ФУНКЦИЯ {node["name"]!r}')
        for idx, arg in enumerate(node["args"], 1):
            lines.append(f"{indent}  аргумент {idx}:")
            _render_arg(arg, indent + "    ", lines)
        return
    lines.append(f"{indent}<неизвестный вид: {kind}>")


def render_text(nodes) -> str:
    lines = []
    for node in nodes:
        if isinstance(node, str):
            lines.append(f'ТЕКСТ: "{node}"')
        else:
            _render_node(node, "", lines)
    return "\n".join(lines)


def _run_self_tests() -> None:
    # Простой символ/подсимвол/аргументы.
    for text, expected in [
        ("{0}", {"kind": "symbol", "object": "0", "object_kind": "index", "subsymbol": None, "args": []}),
        ("{PAWN_possessive}", {"kind": "symbol", "object": "PAWN", "object_kind": "name", "subsymbol": "possessive", "args": []}),
        ("{0_numCase?год:года:лет}", {"kind": "symbol", "object": "0", "object_kind": "index", "subsymbol": "numCase", "args": ["год", "года", "лет"]}),
        ("{USER_gender ? использовал : использовала}", {"kind": "symbol", "object": "USER", "object_kind": "name", "subsymbol": "gender", "args": ["использовал", "использовала"]}),
    ]:
        node, pos = find_construct(text, 0)
        assert pos == len(text), f"{text!r}: consumed {pos}, expected {len(text)}"
        for key, value in expected.items():
            assert node.get(key) == value, f"{text!r}: {key} = {node.get(key)!r}, expected {value!r}"

    # Экранирование: {{0}} -> буквальный текст "{0}" (плюс отдельный литерал "}").
    node, pos = find_construct("{{0}}", 0)
    assert node["kind"] == "escape" and node["literal"] == "{0", node
    assert pos == 4 and node["raw"] == "{{0}", node
    full = parse_text("{{0}}")
    assert full == [{"kind": "escape", "raw": "{{0}", "literal": "{0"}, "}"], full

    # {lookup: {0}; Case; 3} ({{0}} шт) — как в реальном RemoveSliderText.
    full = parse_text("{lookup: {0}; Case; 3} ({{0}} шт)")
    assert full[0]["kind"] == "function" and full[0]["name"] == "lookup", full
    assert full[0]["args"][0]["kind"] == "symbol" and full[0]["args"][0]["object"] == "0", full
    assert full[0]["args"][1] == "Case" and full[0]["args"][2] == "3", full
    assert full[1] == " (", full
    assert full[2]["kind"] == "escape" and full[2]["literal"] == "{0", full

    # replace с одним уровнем вложенности (RoleRequirementLabelSupremeGender).
    node, _ = find_construct('{replace: {0}; "мужчина"-"нужен"; "женщина"-"нужна"}', 0)
    assert node["kind"] == "function" and node["name"] == "replace", node
    assert node["args"][0]["kind"] == "symbol" and node["args"][0]["object"] == "0", node
    assert node["args"][1] == '"мужчина"-"нужен"', node
    assert node["args"][2] == '"женщина"-"нужна"', node

    # replace(lookup(1)) — два уровня вложенности (CannotGenericWork).
    node, _ = find_construct('{replace: {lookup: {1}; Case; 3}; "область"-""}', 0)
    assert node["kind"] == "function" and node["name"] == "replace", node
    inner = node["args"][0]
    assert inner["kind"] == "function" and inner["name"] == "lookup", inner
    assert inner["args"][0]["kind"] == "symbol" and inner["args"][0]["object"] == "1", inner
    assert inner["args"][1] == "Case" and inner["args"][2] == "3", inner
    assert node["args"][1] == '"область"-""', node

    # PawnCount — numCase с четырёхуровневой вложенностью (lookup внутри lookup).
    pawn_count = (
        "{COUNT_numCase ? {lookup: {KINDLABEL}; Case; 4} : "
        "{lookup: {lookup: {KINDLABEL}; Plural; 1}; Case; 4} : "
        "{lookup: {lookup: {KINDLABEL}; Plural; 1}; Case; 4}}"
    )
    node, pos = find_construct(pawn_count, 0)
    assert pos == len(pawn_count), pos
    assert node["kind"] == "symbol" and node["subsymbol"] == "numCase", node
    assert len(node["args"]) == 3, node
    first_arg = node["args"][0]
    assert first_arg["kind"] == "function" and first_arg["name"] == "lookup", first_arg
    assert first_arg["args"][0]["kind"] == "symbol" and first_arg["args"][0]["object"] == "KINDLABEL", first_arg
    second_arg = node["args"][1]
    assert second_arg["kind"] == "function" and second_arg["name"] == "lookup", second_arg
    inner_lookup = second_arg["args"][0]
    assert inner_lookup["kind"] == "function" and inner_lookup["name"] == "lookup", inner_lookup
    assert inner_lookup["args"][0]["object"] == "KINDLABEL", inner_lookup

    # Вложенный '{' до '?'/имени функции — ошибка, а не тихий разбор.
    node, _ = find_construct("{0_{1}}", 0)
    assert node["kind"] == "error", node

    print("Все встроенные проверки прошли успешно.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("text", nargs="?", help="Строка с {...}-конструкцией(-ями). Без аргумента — читается из stdin.")
    parser.add_argument("--json", action="store_true", help="Вывести разбор в виде JSON вместо текстового дерева.")
    parser.add_argument("--self-test", action="store_true", help="Прогнать встроенные проверки на реальных примерах из репозитория и выйти.")
    args = parser.parse_args()

    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    if args.self_test:
        _run_self_tests()
        return

    text = args.text if args.text is not None else sys.stdin.read()
    if not text.strip():
        print("Пустой ввод: передайте строку аргументом или через stdin.", file=sys.stderr)
        sys.exit(1)

    nodes = parse_text(text)
    if args.json:
        print(json.dumps(nodes, ensure_ascii=False, indent=2))
    else:
        print(render_text(nodes))


if __name__ == "__main__":
    main()
