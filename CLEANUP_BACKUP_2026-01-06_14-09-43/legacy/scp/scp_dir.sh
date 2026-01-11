#!/bin/bash
# Usage: ./scp_dir.sh <source_dir> username@<pi_ip:/destination_path

#run "whoami" for username and "hostname -I" for IP address on pi

SOURCE_DIR="$1"
DEST="$2"
IGNORE_FILE="dont_scp"

EXCLUDES=()
if [ -f "$IGNORE_FILE" ]; then
    while read -r line; do
        [ -n "$line" ] && EXCLUDES+=("--exclude=$line")
    done < "$IGNORE_FILE"
fi

rsync -avz "${EXCLUDES[@]}" "$SOURCE_DIR" "$DEST"
