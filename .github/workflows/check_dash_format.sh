#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Checking XML files for correct dash formatting..."

# Find all .xml files recursively
errors=0
while IFS= read -r -d '' file; do
    # Use grep to find lines with wrong format: " - "
    if grep -P -n '(^|[^ ]) - ' "$file"; then
        echo "Invalid dash format found in: $file"
        errors=1
    fi
done < <(find . -type f -name "*.xml" -print0)

if [ "$errors" -ne 0 ]; then
    echo "Invalid dash formats detected. Use non-breaking space + em dash (Alt+0160 + —)."
    exit 1
else
    echo "All XML files use correct dash formatting."
fi
