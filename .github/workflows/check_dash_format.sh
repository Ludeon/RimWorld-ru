#!/bin/bash

set -e

echo "Checking XML files for correct dash formatting..."

errors=0

while IFS= read -r -d '' file; do
    # Проверим файл построчно
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Пропускаем комментарии (строки, начинающиеся с <!-- с возможными пробелами)
        if echo "$line" | grep -q '\s*^<!--'; then
            continue
        fi

        # Ищем " - " (обычный пробел, дефис, пробел)
        if [[ "$line" =~ [^ ] -  ]]; then
            echo "Invalid dash format in $file:"
            echo "$line"
            echo
            errors=1
        fi

        # Ищем " - " (обычный пробел, длинное тире, пробел)
        if [[ "$line" =~ [^ ] —  ]]; then
            echo "Invalid dash format in $file:"
            echo "$line"
            echo
            errors=1
        fi
    done < "$file"
done < <(find . -type f -name "*.xml" -print0)

if [ "$errors" -ne 0 ]; then
    echo "Found invalid dash formats. Use non-breaking space + em dash: Alt+0160 + —"
    exit 1
else
    echo "All XML files use correct dash formatting."
fi
