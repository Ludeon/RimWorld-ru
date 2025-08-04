#!/bin/bash

set -e

echo "Проверка XML файлов на то, что теги с reportString не должны иметь точку в конце"

errors=0

while IFS= read -r -d '' file; do
    file_printed=0
    line_number=0
    # Проверим файл построчно
    while IFS= read -r line || [[ -n "$line" ]]; do
        line_number=$((line_number + 1))
        # Пропускаем комментарии (строки, начинающиеся с <!-- с возможными пробелами)
        if echo "$line" | grep -q '^\s*<!--'; then
            continue
        fi
        # Находим тег с .reportString
        if echo "$line" | grep -q '.reportString>'; then
            # Находим точку перед закрытием тега
            if echo "$line" | grep -q '\.<\/'; then
                if [[ "$file_printed" -eq 0 ]]; then
                    echo "        "
                    echo -e "Файл: \033[1;33m$file\033[0m"
                    file_printed=1
                fi
                echo -e "\033[1;31mТочка в конце reportString\n\033[1;32mстрока $line_number\033[0m: $line"
                errors=1
            fi
        fi
    done < "$file"
done < <(find . -type f -name "*.xml" -print0)

if [ "$errors" -ne 0 ]; then
    echo "Обнаружены ошибки в формате некоторых XML файлах: уберите точку в конце reportString"
    exit 1
else
    echo "Все файлы XML имеют верный формат reportString"
fi
