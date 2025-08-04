#!/bin/bash

set -e

echo "Проверка XML файлов на форматирование неразрывного пробела и тире"

errors=0

while IFS= read -r -d '' file; do
    file_errors=0

    matches=$(perl -ne '
        next if /^\s*<!--/;
        s/<!--.*$//;

        if (/[^ ]- /) {
            print "$.:type=nonbreaking_hyphen:$_";
        }
        if (/ - /) {
            print "$.:type=space_hyphen_space:$_";
        }
        if (/ — /) {
            print "$.:type=space_emdash_space:$_";
        }
    ' "$file")

    if [[ -n "$matches" ]]; then
        echo -e "\nФайл: \033[1;33m$file\033[0m"
        echo "$matches" | while IFS= read -r line; do
            line_number="${line%%:*}"
            rest="${line#*:}"
            type="${rest%%:*}"
            line_content="${rest#*:}"

            case "$type" in
                type=space_hyphen_space)
                    msg="Пробел и дефис"
                    ;;
                type=nonbreaking_hyphen)
                    msg="Неразрывный пробел и дефис (нужно тире —)"
                    ;;
                type=space_emdash_space)
                    msg="Обычный пробел перед тире (нужен неразрывный)"
                    ;;
                *)
                    msg="Неизвестная ошибка"
                    ;;
            esac

            echo -e "\033[1;31m$msg\n\033[1;32m$line_number:\033[0m$line_content"
            errors=1
            file_errors=1
        done
    fi
done < <(find . -type f -name "*.xml" -print0)

if [ "$errors" -ne 0 ]; then
    echo -e "\nОбнаружены ошибки: используйте неразрывный пробел и длинное тире (Alt+0160 + Alt+0151)"
    exit 1
else
    echo "Все файлы XML имеют верный формат тире"
fi
