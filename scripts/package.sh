#!bin/bash

echo "Starting build..."

cd ../

rm -r "./dist"

python -m build

echo "Finished build..."

read -p "Press any key to continue..." x
