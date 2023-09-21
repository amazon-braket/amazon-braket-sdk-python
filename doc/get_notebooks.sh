#!/bin/bash

repo_url="https://github.com/amazon-braket/amazon-braket-examples.git"
branch_name="feature/reorganized-examples"
clone_dir="modules"

temp_dir=$(mktemp -d)

git clone --depth 1 --branch "$branch_name" "$repo_url" "$temp_dir"

rm -rf "$clone_dir"

mv "$temp_dir"/"$clone_dir" "$PWD"

rm -rf "$temp_dir"

echo "Notebooks copied."
