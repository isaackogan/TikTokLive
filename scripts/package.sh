#!/usr/bin/env bash


# Extract version from setup.py
VERSION_TAG="6.3.1"

echo "-> Starting build for version \"$VERSION_TAG\""

echo "-> Updating \"TikTokLive/__version__.py\""

echo "PACKAGE_VERSION: str = \"$VERSION_TAG\"" > ../TikTokLive/__version__.py

echo "-> Updating \"setup.py\""

sed -i '' "s|\"version\": *\"[^\"]*\"|\"version\": \"$VERSION_TAG\"|" "../setup.py"

sed -i '' "s|\"version\": *\"[^\"]*\"|\"version\": \"$VERSION_TAG\"|" "../scripts/docs/manifest.json"

echo "-> Clearing Existent Distribution"

cd ../

rm -r "./dist"

echo "-> Building New Distribution"

echo ls

python -m build

echo "-> Finished build..."

read -p "Press any key to continue..." x
