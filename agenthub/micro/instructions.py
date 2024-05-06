import os
from typing import Dict

instructions: Dict = {}

base_dir = os.path.dirname(os.path.abspath(__file__)) + '/_instructions'
for root, dirs, files in os.walk(base_dir):
    if len(files) == 0:
        continue
    rel_base = os.path.relpath(root, base_dir)
    keys = rel_base.split('/')
    obj = instructions
    for key in keys:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]
    for file in files:
        without_ext = os.path.splitext(file)[0]
        with open(os.path.join(root, file), 'r') as f:
            obj[without_ext] = f.read()
