# Keyed-строки

Применимо к файлам `**/Keyed/*.xml`.

Папки Keyed содержат файлы в формате .xml, содержащие игровые строки в виде наборов "ключ-значение". По структуре Keyed-файл состоит из корневого XML-элемента `LanguageData`, в котором содержится плоская структура XML-элементов:

- Имя элемента является ключом
- Текст внутри этого элемента является значением

Оригинальные Keyed-строки находятся по путям `.Data/**/Keyed/*.xml`. Локализованные — во всех остальных папках Keyed: `**/Keyed/*.xml`.

## Как код обращается к строкам

```csharp
TaggedString Translate(this string key)
TaggedString Translate(this string key, NamedArgument arg1, NamedArgument arg2, ...)  // до 8 штук, либо params NamedArgument[]
```

`NamedArgument` — структура `{ object arg; string label; }`. У неё есть неявное преобразование из большинства игровых типов (`Pawn`/`Thing`, `Def`, `Faction`, `Map`, `IntVec3`, `TargetInfo`, чисел, строк и т.д.), поэтому значение можно передать в `Translate(...)` напрямую, без обёртки — тогда `label` останется `null`. Явно задать `label` можно методом `.Named("ИМЯ")` (определён как extension-метод для тех же типов).

Сами перегрузки `Translate(...)` с аргументами внутри вызывают более низкоуровневый

```csharp
public static TaggedString GrammarResolverSimple.Formatted(TaggedString str, List<string> argsLabelsArg, List<object> argsObjectsArg)
```

который и подставляет аргументы в плейсхолдеры строки.

## Как разрешается плейсхолдер `{...}`

Плейсхолдер в строке выглядит как `{ИДЕНТИФИКАТОР}` или `{ИДЕНТИФИКАТОР_Подсимвол}`. `ИДЕНТИФИКАТОР` разрешается в методе `GrammarResolverSimple.TryResolveInner` так:

1. **Если `ИДЕНТИФИКАТОР` — число N.** Берётся N-й аргумент вызова, считая **все** аргументы подряд по порядку следования в вызове (`argsObjects[N]`), **независимо от того, был ли у этого конкретного аргумента задан `.Named(...)`**. Отсюда плейсхолдеры вида `{0}`, `{1}`, ...
2. **Иначе.** Среди аргументов ищется тот, чей `label` (заданный через `.Named("ИДЕНТИФИКАТОР")`) точно совпадает с `ИДЕНТИФИКАТОР`.

Если после идентификатора есть `_Подсимвол`, для найденного объекта-аргумента вызывается `TryResolveSymbol`: он смотрит на C#-тип объекта (`Pawn`, `Thing`, `Gender` и т.д.) и подставляет соответствующие данные — склонение, род, притяжательную форму и т.п. Полный список Подсимволов по типу — см. [grammar-symbols.md](grammar-symbols.md), либо `python tools/subsymbols.py <Тип>` (актуальнее, генерируется из кода игры).

## Пример (иллюстрация механизма)

В коде есть строка:

```csharp
command_Toggle2.defaultDesc = "BiosculpterAutoAgeReversalDescription".Translate(biotunedTo.Named("PAWN"), taggedString.Named("NEXTTREATMENT"));
```

Ключу `BiosculpterAutoAgeReversalDescription` соответствует строка в `Ideology\Keyed\FloatMenu.xml`:

```xml
<BiosculpterAutoAgeReversalDescription>Разрешить {PAWN_labelShort} проходить ежегодный цикл омоложения в этом биоскульпторе, в соответствии с {PAWN_possessive} убеждениями. {NEXTTREATMENT}</BiosculpterAutoAgeReversalDescription>
```

`{PAWN_possessive}`: `PAWN` — Символ (аргумент с `label == "PAWN"`, т.е. `biotunedTo`), `possessive` — Подсимвол. За обработку Подсимвола `possessive` отвечает ветка в `TryResolveSymbol`, которая для `Pawn` обращается к

```csharp
string GenderUtility.GetPossessive(this Gender gender)
```

Этот метод в зависимости от пола персонажа вернёт результат вызова `"Prohis".Translate()`, `"Proits".Translate()` или `"Proher".Translate()` — то есть Подсимвол сам обращается к другому Keyed-ключу. Этим ключам в `Core\Keyed\Grammar.xml` соответствуют строки `его`, `его` и `её`.

Это показывает, что разрешение Подсимвола может быть рекурсивным: Подсимвол одного Символа иногда сам является обращением к другой Keyed-строке.

## Как узнать, что конкретно подставляется в плейсхолдер

Это отдельная практическая задача (например: "какие значения может принимать `{0_label}` в такой-то строке?") — пошаговый алгоритм для неё см. в [howto-resolve-placeholder.md](howto-resolve-placeholder.md).
