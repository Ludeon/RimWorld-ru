# Символы и подсимволы `GrammarResolverSimple`

Применимо к файлам `**/Keyed/*.xml` и `*/DefInjected/**/*.xml`.

Этот файл — справочник по механизму `{СИМВОЛ_подсимвол}`, описанному на примере в [keyed-strings.md](keyed-strings.md). Он построен по исходнику `.Decompiled/Verse/GrammarResolverSimple.cs` (метод `TryResolveSymbol`).

**Актуальность:** это статичный, вручную выверенный снимок; он может отстать от новой версии игры. Для гарантированно актуального списка по конкретному типу запусти `python tools/subsymbols.py <ТипC#>` — этот скрипт разбирает `TryResolveSymbol` прямо из `.Decompiled` при каждом вызове. При расхождении между этим файлом и выводом скрипта (или самим кодом) следует руководствоваться кодом/скриптом.

## Важно: подсимволы зависят от типа объекта, а не от имени символа

Имя символа (`PAWN`, `RECIPIENT`, `INITIATOR`, `FACTION`, `NEXTTREATMENT`, ...) — это просто метка, которую конкретный вызов в коде даёт аргументу через `.Named("ИМЯ")`. Она не входит в фиксированный список: у каждого вызова `"Ключ".Translate(объект.Named("ИМЯ"), ...)` в декомпилированном коде своё имя. **Набор доступных подсимволов определяется C#-типом переданного объекта**, а не именем.

Поэтому, чтобы узнать, какие подсимволы доступны для конкретной переменной в конкретной строке:

1. Найди в `.Decompiled/**/*.cs` вызов `.Translate(...)` или `GrammarResolverSimple.Formatted(...)`, где этой переменной присваивается имя через `.Named("ИМЯ")` (или через `NamedArgument`, где имя параметра совпадает с именем символа).
2. Определи C#-тип этого аргумента.
3. Найди этот тип в таблице ниже (или через `python tools/subsymbols.py`) — это и есть полный список подсимволов, доступных для переменной в данной строке.

Если объект — это `Pawn`, а его назвали `RECIPIENT` вместо `PAWN` — доступны всё равно подсимволы из таблицы `Pawn`, никакой отдельной семантики за именем `RECIPIENT` не стоит.

## Таблица подсимволов по типу объекта

Подсимвол `""` (то есть просто `{ИМЯ}` без `_подсимвол`) везде означает "значение по умолчанию" для этого типа.

### `Pawn` (персонаж)

`""`/`nameDef`, `nameFull`, `nameFullDef`, `label`, `labelNoParenthesis`,
`labelShort`, `definite`, `indefinite`, `nameIndef`, `parentage`,
`pronoun`, `possessive`, `objective`, `genderNoun`, `gender`,
`genderResolved`, `humanlike`,
`factionName`, `factionPawnSingular(Def|Indef)`,
`factionPawnsPlural(Def|Indef)`, `factionRoyalFavorLabel`,
`kind`, `kindDef`, `kindIndef`, `kindPlural(Def|Indef)`,
`kindBase`, `kindBase(Def|Indef)`, `kindBasePlural(Def|Indef)`,
`race`, `raceDef`, `raceIndef`,
`lifeStage`, `lifeStageDef`, `lifeStageIndef`, `lifeStageAdjective`,
`legalStatus`,
`title`, `titleDef`, `titleIndef`,
`bestRoyalTitle(Def|Indef)`, `royalTitleInCurrentFaction(Def|Indef)`,
`age`, `age_numCase`, `chronologicalAge`, `ageFull`,
`relationInfo`, `relationInfoInParentheses`,
`xenotype`.

Пример из `keyed-strings.md`: `{PAWN_possessive}` — подсимвол `possessive` вызывает `Gender.GetPossessive()`, которая для рода персонажа подставляет Keyed-ключ `Prohis`/`Proits`/`Proher` (см. `Core/Keyed/Grammar.xml`).

### `Thing` (предмет/существо на карте)

`""`, `label`, `labelCap`, `labelNoParenthesis(Def|Indef)`, `labelPlural(Def|Indef)`, `labelShort(Def|Indef)`, `definite`, `indefinite`, `pronoun`, `possessive`, `objective`, `factionName`, `gender`, `quality`.

### `Hediff` (состояние здоровья/ранение/болезнь)

`""`, `label`, `labelNoun`.

### `WorldObject` (объект на карте мира)

`""`, `label`, `labelCap`, `labelPlural(Def|Indef)`, `definite`, `indefinite`, `pronoun`, `possessive`, `objective`, `factionName`, `gender`.

### `Faction` (фракция)

`""`/`name`, `pawnSingular(Def|Indef)`, `pawnsPlural(Def|Indef)`, `royalFavorLabel`, `leaderNameDef`, `leaderPossessive`, `leaderObjective`, `leaderPronoun`.

### `Ideo` (идеология)

`""`/`name`, `memberName`, `memberNamePlural`, `memberName(Def|Indef)`, `adjective`.

### `Precept` (принцип идеологии)

`""`/`label`/`name`, `labelIndef`, `labelCap`, `labelCapIndef`, `labelDef`, `labelCapDef`.

### `Def` (любой деф — общий случай) и `PawnKindDef`

Общие для любого `Def`: `""`, `label`, `labelPlural(Def|Indef)`, `definite`, `indefinite`, `pronoun`, `possessive`, `objective`, `gender`.

Дополнительно только для `PawnKindDef`: `labelPlural`, `labelPluralDef`, `labelPluralIndef` (переопределены отдельно от общих `Def`).

### `RoyalTitle` (титул)

`""`/`label`, `indefinite`.

### `string` (обычная строка/слово)

`""`, `plural`, `plural(Def|Indef)`, `definite`, `indefinite`,
`pronoun`, `possessive`, `objective`, `gender`,
`replace` (принимает аргументы через `?`, см. ниже),
`numCase` (принимает аргументы через `?`, см. ниже).

### `int` / `long` / `float` (число)

`""`, `ordinal`, `multiple` (аргументы через `?`), `numCase` (аргументы через `?`), `percentage`, `percentageEmptyZero`, `time`.

## Подсимволы с аргументами (`{СИМВОЛ_подсимвол?арг1:арг2:...}`)

Некоторые подсимволы принимают дополнительные аргументы через `?`, разделённые `:` — их количество и смысл фиксированы под конкретный
подсимвол, а не произвольны:

- `gender?мужскойВариант:женскийВариант` или `gender?мужскойВариант:женскийВариант:безРодовойВариант` (2 или 3 аргумента) — подставляет нужный вариант текста по роду.
- `humanlike?вариантДляЛюдей:вариантДляЖивотных` (ровно 2 аргумента).
- `multiple?формаМного:формаОдин` (ровно 2 аргумента, по числу > 1 или нет).
- `numCase?вариант1:вариант2:...` — число аргументов равно `LanguageWorker.TotalNumCaseCount` активного языка (для русского — **3**: соответствует числовому согласованию "1 / 2-4 / 5+", например `{DAYS_numCase?день:дня:дней}`). **Это не то же самое, что грамматический падеж** (падежный словарь `WordInfo/Case.txt` — отдельный механизм, задокументирован отдельно, не через `numCase`).

## Функции (`{имяФункции:арг1;арг2;...}`)

Отдельный, третий вид конструкции в фигурных скобках — вызов функции; синтаксис похож на символ, но распознаётся по `:` сразу после имени и использует `;` как разделитель аргументов. Определены в `Verse/LanguageWorker.cs` (`ResolveFunction`):

- `{lookup:слово;ИмяТаблицы;индекс}` — ищет `слово` в таблице `WordInfo` проекта (например, таблица `Case` — падежный словарь `Case.txt`, `индекс` — номер столбца/формы) и подставляет найденное значение; индекс необязателен (по умолчанию `1`). Это основной способ подставить словоформу из падежного или иного словаря `WordInfo` прямо в Keyed/DefInjected-строку.
- `{replace:слово;паттерн1=замена1;паттерн2=замена2;...}` — берёт `слово` и заменяет в нём первый подошедший паттерн.

Полное описание таблиц `WordInfo` (`Case`, `Gender/*`, `Plural`, `Imperfect`, `SkillDef_subject`) и работы с падежным словарём, а также CLI-инструмент для проверки покрытия слова в этих таблицах — тема будущей доработки (см. `tools/subsymbols.py` как образец подхода: генерировать справочник из кода/данных, а не поддерживать его вручную).
