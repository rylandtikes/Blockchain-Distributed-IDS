i#!/bin/bash

while IFS= read -r package || [ -n "$package" ]; do
    # Skip empty lines and comments
    [[ "$package" =~ ^#.*$ || -z "$package" ]] && continue

    # Extract just the package name (strip version specifiers)
    pkg_name=$(echo "$package" | cut -d= -f1 | cut -d\< -f1 | cut -d\> -f1 | xargs)

    # Check if it's already installed
    if pip show "$pkg_name" > /dev/null 2>&1; then
        echo "already installed: $pkg_name"
    else
        echo "installing: $package"
        pip install "$package" || echo "failed: $package"
    fi
done < requirements.txt

