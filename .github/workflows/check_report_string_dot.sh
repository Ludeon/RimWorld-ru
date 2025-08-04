#!/bin/bash

set -e

echo "Проверка XML файлов на наличие точки в конце reportString"

errors=0

while IFS= read -r -d '' file; do
    matches=$(perl -ne '
        next if /^\s*<!--/;  # Пропустить комментарии
        if (/.*\.reportString>([^<]*)\.<\/.*>/) {
            printf "%d:%s", $., $_;
        }
    ' "$file")
    
    if [[ -n "$matches" ]]; then
        echo -e "\nФайл: \033[1;33m$file\033[0m"
        echo -e "$matches" | while IFS= read -r line; do
            # Разделить строку: до двоеточия — номер строки, после — содержимое
            line_number="${line%%:*}"
            line_content="${line#*:}"
            echo -e "\033[1;32m$line_number:\033[0m $line_content"
        done
        errors=1
    fi
done < <(find . -type f -name "*.xml" -print0)

if [ "$errors" -ne 0 ]; then
    echo -e "\nОбнаружены ошибки: уберите точку в конце reportString"
    exit 1
else
    echo "Все файлы XML имеют верный формат reportString"
fi
