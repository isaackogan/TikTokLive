#!/bin/bash

# Create api-doc files
#sphinx-apidoc --ext-autodoc --force -o  . ../../TikTokLive && ^

echo "Generated API docs"

# Generate the html
.\\make.bat html

echo "Made HTML"

# Add nojekyll
cp ./.nojekyll ./build/html/.nojekyll

echo "Copied .nojekyll"

# Remove old folder
rm -r ../../docs

echo "Removed old docs"

# Copy the html folder
cp -r ./build/html ../../docs

echo "Moved to docs folder"

echo "Build docs finished!"

read -p "Press any key to continue" x
