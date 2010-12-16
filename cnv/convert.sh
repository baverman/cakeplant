#!/bin/sh
# Usage convert.sh /path/to/mdb {convert.py|convert2.py} account

rm *.csv
mdb-tables -1 "$1" | xargs -d '\n' -n1 --replace=^ echo "mdb-export \"$1\" \"^\" > \"^.csv\"" | sh
python `dirname $0`/$2 $3
