#!bin/bash

echo "Starting build..."

cd ../

python -m build

echo "Finished build..."

read -p "Press any key to continue..." x
