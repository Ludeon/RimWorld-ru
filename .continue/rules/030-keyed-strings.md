---
description: Как работают Keyed-строки
globs: "**/Keyed/*.xml"
---

# Keyed-строки

Папки Keyed содержат файлы в формате .xml, содержащие игровые строки на в виде наборов "ключ-значение". По структуре Keyed-файл состоит из корневого XML-элемента `LanguageData`, в котором содержится плоская структура XML-элементов:

- Имя элемента является ключом
- Тест внутри этого элемента является значением

В коде доступ к этим данным осуществляется через методы расширения вида:

```csharp
TaggedString Translate(this string key, NamedArgument arg1, NamedArgument arg2...)
```

или через метод

```csharp
	public static TaggedString GrammarResolverSimple.Formatted(TaggedString str, List<string> argsLabelsArg, List<object> argsObjectsArg)
```

Эти методы обращаются за локализованной или оригинальной строкой, в зависимости от выбранного в игре языка:

- Оригинальные Keyed-строки находятся по путям `.Data/**/Keyed/*.xml`
- Локализованные Keyed-строки находятся во всех остальных папках Keyed: `**/Keyed/*.xml`

### Пример

В коде есть строка 

```csharp
	command_Toggle2.defaultDesc = "BiosculpterAutoAgeReversalDescription".Translate(biotunedTo.Named("PAWN"), taggedString.Named("NEXTTREATMENT"));
```

Игра обращается к Keyed-строке по ключу `BiosculpterAutoAgeReversalDescription`. Это значит, что где-то в проекте существует Keyed-файл с элементом `BiosculpterAutoAgeReversalDescription`. И действительно, поиском по всем .xml файлам в папках Keyed локализации можно найти такой элемент в файле `Ideology\Keyed\FloatMenu.xml`:
```xml
  <BiosculpterAutoAgeReversalDescription>Разрешить {PAWN_labelShort} проходить ежегодный цикл омоложения в этом биоскульпторе, в соответствии с {PAWN_possessive} убеждениями. {NEXTTREATMENT}</BiosculpterAutoAgeReversalDescription>
```
    
В этой строке есть конструкиця `{PAWN_possessive}`. В ней `PAWN` это символ, а `possessive` - подсимвол. 

- Символ `PAWN` указывает, что вместо этой конструкции нужно подставить данные персонажа, полученного в коде через `biotunedTo.Named("PAWN")`. 
- Подсимвол `possessive` указывает, какие именно данные нужно подставить. Этим занимается метод `TryResolveSymbol` в классе `GrammarResolverSimple`. 

В данном примере в `TryResolveSymbol` в обработчике подсимвола `possessive` идёт обращение к методу 

```csharp
string GenderUtility.GetPossessive(this Gender gender)
```

, который в зависимости от пола персонажа, подставит строку `"Prohis".Translate()`, `"Proits".Translate()` или `"Proher".Translate()` 

Игра вновь обращается к Keyed-строке, но на этот раз по ключу `Prohis`, `Proits` или `Proher`, соответственно. Поиском по этим ключам по всем .xml файлам в папках Keyed локализации можно найти, что в файле `Core\Keyed\Grammar.xml` этим ключам соответствуют строки `его`, `его` и `её`.