#!/usr/bin/env zsh

# https://docs.python.org/3/tutorial/venv.html

python3 -m venv venv; . venv/bin/activate; pip install -r requirements.txt --upgrade
