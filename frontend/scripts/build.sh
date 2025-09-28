#!/bin/bash


# check current directory is frontend
if [ "$(basename "$(pwd)")" != "frontend" ]; then
    echo "Error: Current directory is not frontend"
    exit 1
fi

# build frontend
flutter build web

