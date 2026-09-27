# Что подставляется в плейсхолдер

Открывай этот файл, когда нужно понять, какие значения реально окажутся на месте `{0}`, `{ИМЯ}` или `{ИМЯ_подсимвол}` в конкретной строке, например чтобы согласовать род, число или падеж.

Механизм один для Keyed-строк и для полей дефов (DefInjected): в каком-то месте кода у строки вызывается `.Translate(...)` или `.Formatted(...)` с аргументами. Отличается только шаг 1.

## Шаг 0: проверить наличие кода игры

В папке `.Decompiled/` должен лежать файл `Assembly-CSharp.csproj`. Если его нет, скажи об этом прямо и дальше не продолжай.

## Шаг 1: найти место вызова

- **Keyed-строка** (`Keyed/*.xml`): грепом по `.Decompiled/**/*.cs` найди `"ИмяКлюча".Translate(`.
- **Поле дефа** (`DefInjected/ТипДефа/*.xml`): по [def-injected.md](def-injected.md) определи деф и поле. Затем найди в коде, где это поле читается (например, `Props.message`, `def.description`), и проверь, вызывается ли на нём `.Formatted(...)`.
- Если мест вызова несколько, разбери каждое: на одну и ту же позицию разные места могут передавать разные объекты.
- Если вызов не нашёлся, строка может собираться в два этапа (`.Formatted` вызывается в другом месте) или ключ формируется динамически. Скажи прямо, что прямого вызова нет, и перечисли, что удалось выяснить.

## Шаг 2: сопоставить плейсхолдер с аргументом

Процитируй точный текст плейсхолдера и выполни:

```
python tools/parse_placeholder.py "{точный текст}"
```

Используй результат разбора скрипта (Символ, Подсимвол, Аргументы). Правила разбора описаны в
[placeholder-syntax.md](placeholder-syntax.md).

По Символу найди аргумент вызова:

- `{N}` (число) — аргумент с номером N (счёт с 0) среди **всех** аргументов, включая те, у которых есть `.Named(...)`. В `"Key".Translate(a.Named("PAWN"), b)` `{0}` — это `a` (он же `{PAWN}`), а `{1}` — это `b`.
- `{ИМЯ}` — аргумент с `.Named("ИМЯ")`. Аргумент без `.Named` доступен только как `{N}`.

## Шаг 3: определить C#-тип аргумента

Возможные значения определяет **тип** объекта, а не имя Символа. `PAWN`, `RECIPIENT`, `INITIATOR` — это просто метки из `.Named(...)`: если объект — `Pawn`, ему доступны Подсимволы `Pawn` при любом имени.

- Найди тип по объявлению переменной или параметра в месте вызова.
- Если это параметр метода, грепом найди, откуда вызывается метод: там видно, какие сущности реально передаются.
- Если тип общий (`Pawn`, `Thing`) и связан с компонентом (`CompXxx`/`CompProperties_Xxx`), найди в `.Data/<DLC>/Defs/**`, у каких дефов этот комп указан в `<comps>`. Так получится точный список сущностей.

## Шаг 4: разобрать Подсимвол (если есть)

Выполни `python tools/subsymbols.py <Тип>` и убедись, что Подсимвол из шага 2 есть в списке для этого типа. Что именно он подставляет, смотри в ветке `case "<подсимвол>":` для этого типа в `TryResolveSymbol` (`.Decompiled/Verse/GrammarResolverSimple.cs`).

## Шаг 5: проверить рекурсию

Подсимвол может сам обращаться к другому Keyed-ключу. Открой ветку `case "<подсимвол>":` из шага 4 и проверь, нет ли в ней (или в вызываемом из неё методе) `"Ключ".Translate()`. Если есть, повтори шаги 1–4 для этого ключа. Если такого вызова нет, рекурсии нет. Пример рекурсии: `{PAWN_possessive}` вызывает `GenderUtility.GetPossessive`, а та возвращает `"Prohis"`/`"Proher"`/`"Proits"`.Translate(), то есть `его`/`её`/`его` из `Core/Keyed/Grammar.xml`.

## Шаг 6: указать источник

В ответе укажи файл и строку **каждого** места вызова, откуда взят вывод. Если места вызова передают разные типы, покажи их все. Не делай выводов по имени ключа, поля или по комментарию. Файл, строку и тип бери только из того, что grep или чтение файла вернули в этом ответе.

---

Примеры ниже — иллюстрации. Для новой строки путь, место вызова и тип находи заново, не переноси их из примера.

## Пример 1: Keyed

`Anomaly/Keyed/FloatMenu.xml`:

```xml
<FloatMenuContainmentRequires>{0_label} требует:</FloatMenuContainmentRequires>
```

1. Grep находит **два** вызова:
   - `FloatMenuOptionProvider_CarryingPawn.cs`: `"FloatMenuContainmentRequires".Translate(carriedPawn).ToLower()`;
   - `StudyUtility.cs`: `"FloatMenuContainmentRequires".Translate(entity).CapitalizeFirst()`.
2. В обоих вызовах `{0}` — первый и единственный аргумент.
3. Типы: `carriedPawn` — `Pawn` (существо, которое несут в место изоляции), `entity` — `Thing` (параметр метода `TargetHoldingPlatformForEntity`).
4. `label` есть и у `Pawn`, и у `Thing`: это отображаемое название существа.
5. Ветка `case "label":` для `Pawn` — `resolvedStr = pawn.LabelNoCountColored;`, для `Thing` — `resolvedStr = thing.Label;`. Вызова `.Translate()` в них нет, значит рекурсии нет.
6. Источники:

   | Место вызова | `{0}` | Тип | Ветка `label` |
   |---|---|---|---|
   | `.Decompiled/RimWorld/FloatMenuOptionProvider_CarryingPawn.cs:210` | `carriedPawn` | `Pawn` | `.Decompiled/Verse/GrammarResolverSimple.cs:328` |
   | `.Decompiled/RimWorld/StudyUtility.cs:85` | `entity` (параметр, строка 13) | `Thing` | `.Decompiled/Verse/GrammarResolverSimple.cs:576` |

Итог: на месте `{0_label}` будет название существа, которое помещают в место изоляции. В коде оно может прийти как `Pawn` или как `Thing`.

## Пример 2: DefInjected

`Anomaly/DefInjected/HediffDef/Hediffs_Global_Misc.xml`:

```xml
<DuplicateSickness.comps.HediffComp_MessageAboveSeverity.message>{0_nameDef} недомогает из-за дупликации.</DuplicateSickness.comps.HediffComp_MessageAboveSeverity.message>
```

1. Путь: деф `DuplicateSickness` → список `comps` → элемент по имени `HediffComp_MessageAboveSeverity` (см. «Путь инъекции» в [def-injected.md](def-injected.md)) → поле `message`. Оно читается в `HediffComp_MessageAboveSeverity.CompPostTickInterval`:  `Messages.Message(Props.message.Formatted(base.Pawn), ...)`.
2. `{0}` → `base.Pawn`.
3. Тип — `Pawn`: носитель хеддифа, у которого тяжесть превысила порог.
4. `nameDef` у `Pawn` — имя персонажа.
5. Ветка `case "nameDef":` для `Pawn` — `Find.ActiveLanguageWorker.WithDefiniteArticle(pawn.Name.ToStringShort, ...)`, а если имени нет `pawn.KindLabelDefinite()`. Вызова `.Translate()` в ней нет, значит рекурсии нет.
6. Источники:
   - вызов `.Formatted(...)`: `.Decompiled/Verse/HediffComp_MessageAboveSeverity.cs:17`;
   - ветка `nameDef`: `.Decompiled/Verse/GrammarResolverSimple.cs:344`.

Итог: на месте `{0_nameDef}` будет короткое имя носителя хеддифа, а у безымянного существа — название его вида (`KindLabel`).
