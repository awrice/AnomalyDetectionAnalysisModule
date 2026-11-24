if [ -d algorithms/$1 ]; then
    echo "It looks like there is already an algorithm called '$1'! Delete this folder in ADAM/algorithms and try again."
    exit 1
fi

mkdir algorithms/$1
echo "[]" > algorithms/$1/requirements.json
mkdir algorithms/$1/results
cat <<EOF > algorithms/$1/run.sh
#!/bin/bash

DATASET=\$1
PARAMETERS=\$2
OUTPUT_FILE="res.csv"

SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"



### RUN YOUR SCRIPT HERE ###
# Your script should run and output its predictions to \$OUTPUT_FILE. Make sure, if there is any printed output from your script, pipe it to STDERR using >&2 (all STDOUT from run.sh must be json parsable)
# For example: 
# "\$SCRIPT_DIR/.env/bin/python" \$SCRIPT_DIR/my_algorithm.py \\
#     -d "\$DATASET" \\
#     -p "\$PARAMETERS" \\
#     -o "\$SCRIPT_DIR/results/\$OUTPUT_FILE" >&2



STATUS=\$?
if [ \$STATUS -ne 0 ]; then
    exit \$STATUS
fi

# Output to stdout to return the metadata required
echo "{\\"status\\": \\"success\\", \\"output\\": \\"\$OUTPUT_FILE\"}"
EOF