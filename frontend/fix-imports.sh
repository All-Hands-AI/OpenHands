#!/bin/bash
find . -type f -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/from "#\//from "~\//g'
find . -type f -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/import("#\//import("~\//g'