#!/bin/bash

export SHELL=/bin/bash

umask 0002

TTYREC=/opt/pyRMA/bin/ttyrec

file_rec=$(id -u -n)_$(date +%Y-%m-%d_%H:%M:%S.%s)
file_path=/data/pyRMA/filerecords/$(date +%Y/%m/%d)

export file_rec file_path

mkdir -p "$file_path"

$TTYREC -e "/usr/bin/python3 /opt/pyRMA/bin/pyrma.py" "$file_path"/"$file_rec"
