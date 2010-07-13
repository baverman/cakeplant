#!/bin/sh

mdb-tables -1 "$1" | xargs -n1 --replace=^ echo "mdb-export \"$1\" ^ > ^.csv" | sh
python convert.py
