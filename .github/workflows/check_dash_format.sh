#!/bin/bash

set -e

echo "Проверка XML файлов на форматирование неразрывного пробела и тире"

mapfile -d '' files < <(find . -type f -name "*.xml" -print0)

errors=0

process_matches() {
    local file="$1"
    local matches="$2"
    local line line_number rest type line_content msg

    echo -e "\nФайл: \033[1;33m$file\033[0m"

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

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
    done <<< "$matches"
}

for file in "${files[@]}"; do
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
        process_matches "$file" "$matches"
    fi
done

if [ "$errors" -ne 0 ]; then
    echo -e "\nОбнаружены ошибки. Нужно использовать неразрывный пробел и длинное тире (Alt+0160 + Alt+0151)"
    exit 1
else
    echo "Все файлы XML имеют верный формат тире"
fi
