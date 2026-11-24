#!/bin/bash

DATASET=$1
PARAMETERS=$2
OUTPUT_FILE="res.csv"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/.env/bin/python" $SCRIPT_DIR/alg2.py \
    -d "$DATASET" \
    -p "$PARAMETERS" \
    -o "$SCRIPT_DIR/results/$OUTPUT_FILE" >&2

STATUS=$?
if [ $STATUS -ne 0 ]; then
    exit $STATUS
fi

# Output to stdout to return the metadata required
echo "{\"status\": \"success\", \"output\": \"$OUTPUT_FILE\"}"
