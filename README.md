# RimWorld-RU
﻿Здравствуйте, уважаемые игроки RimWorld!

В данном репозитории лежит не что иное, как официальная русская локализация RimWorld и дополнения Royalty. Именно из этого репозитория русский перевод попадает в игру с каждым выходом очередного обновления.

Данный перевод постоянно исправляется и дорабатывается. И если вам не хочется ждать следующего обновления игры, вы можете скачать актуальную версию отсюда.

## Установка

### Стандартный способ

1. Скачать архив, **соответствующий вашей версии игры (это важно!):**
	* Последняя актуальная 1.3 + Royalty + Ideology: [архив](https://github.com/Ludeon/RimWorld-ru/archive/master.zip)
	* 1.2.2900 + Royalty: [архив](https://github.com/Ludeon/RimWorld-ru/archive/release-1.2.2900.zip)
	* 1.1.2654 + Royalty: [архив](https://github.com/Ludeon/RimWorld-ru/archive/release-1.1.2654.zip)
	* Release: [1.0](https://github.com/Ludeon/RimWorld-ru/archive/release-1.0.2150.zip)
	* Beta: [B-18](https://github.com/Ludeon/RimWorld-ru/archive/beta-18.zip), [B-19](https://github.com/Ludeon/RimWorld-ru/archive/beta-19.zip)
	* Alpha : [A-15](https://github.com/Ludeon/RimWorld-ru/archive/alpha-15.zip), [A-16](https://github.com/Ludeon/RimWorld-ru/archive/alpha-16.zip), [A-17](https://github.com/Ludeon/RimWorld-ru/archive/alpha-17.zip)

2. **(Для версий 1.1.*)** Подменить папки локализации папками из архива:
	
	В папку `<путь к папке игры>\Data\Core\Languages\` нужно положить папку `Core` из архива и переименовать её в `Russian`.

	В папку `<путь к папке игры>\Data\Royalty\Languages\` нужно положить папку `Royalty` из архива и переименовать её в `Russian`.

	В папку `<путь к папке игры>\Data\Ideology\Languages\` нужно положить папку `Ideology` из архива и переименовать её в `Russian`.

	Если среди папок локализации были старые папки с тем же именем, их следует удалить и на их место положить новые, под старым именем.

	После ваших действий файлы локализации (например, LanguageInfo.xml) должны находиться **непосредственно** в папке `<путь к папке игры>\Data\Core\Languages\Russian`.
  
	**В версиях игры до 1.0 включительно** файлы локализации должны находиться в папке `<путь к папке игры>\Mods\Core\Languages\Russian`

3. В игре заново выбрать русский язык.

Путь к папке игры для Steam-версии в различных ОС:
* Windows: `C:\Program Files (x86)\Steam\SteamApps\common\RimWorld\`
* Linux: `~/.steam/steam/steamapps/common/Rimworld`
* Mac: `~/Library/Application Support/Steam/steamapps/common/RimWorld/RimWorldMac.app` (для дальнейшей навигации выбрать пункт контекстного меню «Показать содержимое пакета»).

Таким образом, для Steam-версии в ОС Windows полный путь может выглядеть примерно так:`C:\Program Files (x86)\Steam\SteamApps\common\RimWorld\Data\Core\Languages\Russian`  

### Автоматизированный способ

Если не хочется проделывать каждый раз однотипные действия, можете воспользоваться .ps скриптом (только для Windows 10). При запуске скрипт скачает архив с последней версией перевода и положит в нужные папки:

```
powershell.exe -Command "Invoke-WebRequest -OutFile ./master.zip https://github.com/Ludeon/RimWorld-ru/archive/master.zip
powershell.exe "Add-Type -A 'System.IO.Compression.FileSystem';[IO.Compression.ZipFile]::ExtractToDirectory('master.zip', '1');"
RD /s /q "Data\Core\Languages\Russian (Русский)\"
RD /s /q "Data\Royalty\Languages\Russian (Русский)\"
RD /s /q "Data\Ideology\Languages\Russian (Русский)\"
del "Data\Core\Languages\Russian (Русский).tar"
del "Data\Royalty\Languages\Russian (Русский).tar"
del "Data\Ideology\Languages\Russian (Русский).tar"
xcopy "1\RimWorld-ru-master\Core" "Data\Core\Languages\Russian (Русский)\"  /H /Y /C /R /S
xcopy "1\RimWorld-ru-master\Royalty" "Data\Royalty\Languages\Russian (Русский)\"  /H /Y /C /R /S
xcopy "1\RimWorld-ru-master\Ideology" "Data\Ideology\Languages\Russian (Русский)\"  /H /Y /C /R /S
RD /s /q 1
del master.zip
```
Скрипт нужно сохранить в файл с расширением .bat и положить корневую папку игры. Перед запуском убедитесь, что ваша версия игры соответствует версии перевода.

Автор скрипта — Torin Douglas

## Переводчики

### Активные
* [Elevator89](https://github.com/Elevator89)
* [Kamadz](https://github.com/Kamadz)
* [EcherArt](https://github.com/EcherArt)
* [Dimonasdf](https://github.com/Dimonasdf)

### Сделавшие весомый вклад в прошлом
* [Dandi](https://github.com/Dandi91)
* [Humort](https://github.com/Humort)
* [Tarakanhb](https://github.com/Tarakanhb)
* [AcDie](https://github.com/AcDie)
* [Arex-rus](https://github.com/Arex-rus)

## Желающим помочь проекту:
Процесс перевода и организация командной работы описаны в [wiki](https://github.com/Ludeon/RimWorld-ru/wiki).

Обсуждение всех вопросов происходит в [чате Телеграма](https://t.me/joinchat/CEY0QEO8s3S-29d_uv1SaQ) и в [группе ВКонтакте](https://vk.com/rimworld_russian).

Тема на официальном форуме разработчика, посвящённая переводам: http://ludeon.com/forums/index.php?topic=2933.0
