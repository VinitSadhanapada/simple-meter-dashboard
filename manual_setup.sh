#!/bin/bash

if [ ! -d "venv1" ]; then
    echo "Creating local virtual environment..."
    python -m venv venv1
fi

source venv1/bin/activate

pip install --no-index --find-links=packages_folder/ -r requirements.txt

