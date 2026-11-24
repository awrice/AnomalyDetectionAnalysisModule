# ADAM: Anomaly Detection Analysis Module

ADAM is a package designed to run any anomaly detection algorithm in any language or any environment against any dataset. The steps of the process are as follows:

1. You want to run algorithm X with dataset Y with these parameters
2. You create a configuration file called 'myconfig.json' in the configs folder and populate it with "dataset_name", "algorithm_name" and "parameters"
3. Run `main.py --config myconfig` — Subprocess for the algorithm begins and the configurations are passed in. All the files/metadata are in a standardized structure that every algorithm depends on
4. Algorithm returns its predictions in a standard form of csv with metadata
5. Predicted labels and real labels are compared and metrics are calculated

# Description of File Structure

## datasets
Every dataset has its own folder. From here on out, the word 'dataset' will refer to the folder within the 'datasets' directory that has the same name as the value of the 'dataset_name' field in the config file. If there is no such folder, an error is thrown. Sub-folders within datasets are allowed (for example, I might have a folder of all the Logan River Observatory data, and subfolders for each year). Inside each dataset must be at least a single file called data.csv (other files are allowed, but are expected to be specified in the parameters in the config file). The data.csv file contains at least 3 columns: timestamp, value, and label (likewise, other columns are allowed, but should be specified in the parameters in the config file). 

Shown graphically, the datasets folder should have a similar structure to this:
```text
ADAM
 └──datasets
     ├── ...
     ├──dataset123
     ├──mydataset
     │   ├──data.csv
     │   └── ... [*other files if needed] ...
     ├──mydataset_with_subfolders
     │   ├──data.csv
     │   ├──sub_dataset1
     │   │   ├──data.csv
     │   │   └── ... [*other files if needed] ...
     │   └──sub_dataset2
     │       ├──data.csv
     │       └── ... [*other files if needed] ...
     ├──datasetABC
     └── ...
*All files that are NOT data.csv in a dataset should either be specified in the parameters field in the config file, or they should be expected to be ignored.
```

In this example, we can run any configuration with the following "dataset_name" fields (assuming all other fields are also valid):

```json
"dataset_name": "mydataset"
"dataset_name": "mydataset_with_subfolders"
"dataset_name": "mydataset_with_subfolders/sub_dataset1"
"dataset_name": "mydataset_with_subfolders/sub_dataset2"
```
Note that since "mydataset_with_subfolders" has its own data.csv file, it can be properly run against any algorithm. If a collection of datasets does NOT have its own data.csv file, it cannot be used as its own dataset.

## configs
Configurations are defined using JSON. Each configuration must contain the following fields: "dataset_name", "algorithm_name", and "parameters". If not self-explanatory, "dataset_name" defines what subfolder of "ADAM/datasets" should be drawn from as the dataset. "algorithm_name" defines what subfolder in "ADAM/algorithms" should be drawn from to find the algorithm we want to use. "parameters" sets up any other parameters more specific to your algorithm that need to be defined but cannot be generalized across all algorithms in the ADAM toolset (e.g., you have hyperparameters that you'd like to set for a neural net -- since not all algorithms need these hyperparameters, they are not required, but your specific algorithm cannot be run without them). Note that the parameters objects that are passed into an algorithm must be of type dictionary, and inside the "parameters" object can only be primitive types (str, number, boolean, null, arrays and dictionaries), so objects passed into an algorithm must always be serializable. A few examples of valid config files is shown below.

```json
{
    "dataset_name": "lro/lro1", // uses a subfolder in the lro directory -- full path to 
                                // our data would be "ADAM/datasets/lro/lro1/data.csv"
    "algorithm_name": "alg2", // leads us to "ADAM/algorithms/alg2/run.sh"
    "parameters": {
        "hey": "bam",
        "who": [1, 2, 3],
        "where": {"a": 1, "b": 2}
    }
}
```

```json
{
    "dataset_name": "datasetABC", // leads us to "ADAM/datsets/datasetABC/data.csv"
    "algorithm_name": "iforest", // leads us to "ADAM/algorithms/iforest/run.sh"
    "parameters": {} // no parameters should be represented as an empty dictionary
}
```

### Configurations with multiple datasets/algorithms

It is also possible to run any number of algorithms against any number of datasets. In the case of multiple datasets, we need only change a single thing: instead of a string, we change "dataset_name" to a list, populated with all the datasets we're interested in, as shown in example 1. In the case of multiple algorithms being run against one or multiple datasets, a bit more complexity is introduced. Since each algorithm needs it's own parameters, we now require "parameters" to be a list of dictionaries the same length as "algorithm_name". This is validated before anything is run, and if there is a mismatch of length between the "algorithm_name" and the "parameters" lists, an Error is thrown. See Example 2 and 3.

**Example 1**: One algorithm is tested against datasets ds1, ds2, and ds3. No parameters are given.
```json
{
    "dataset_name": ["ds1", "ds2", "ds3"], 
    "algorithm_name": "a1", // leads us to "ADAM/algorithms/a1/run.sh"
    "parameters": {} // no parameters should be represented as an empty dictionary
}
```
**Example 2**: Algorithms a1, a2, and a3 are all run against ds1. Parameters vary -- a1 and a2 are not given any parameters, a3 is given a dictionary
```json
{
    "dataset_name": "ds1", 
    "algorithm_name": ["a1", "a2", "a3"],
    "parameters": [
        {}, // no parameters are given to a1
        {}, // no parameters are given to a2
        {"a": 1, "b": 2, "c": 3} // a small dictionary is given to a3
    ]
}
```
**Example 3**: Algorithms a1, a2, and a3 are each run against ds1, ds2, ds3, and ds4. Parameters vary. This configuration proceeds to run 12 subprocesses total -- running each of our 3 algorithms against 4 datasets. 
```json
{
    "dataset_name": ["ds1", "ds2", "ds3", "ds4"], 
    "algorithm_name": ["a1", "a2", "a3"],
    "parameters": [
        { // a1 is given a dictionary of values
            "hey": "bam",
            "who": [1, 2, 3],
            "where": {"a": 1, "b": 2}
        },
        {}, // a2 is not given any parameters
        { // a3 is given a list of numbers
            "yo": [1, 2, 3, 4, 5, 6, 7, 8]
        }
    ]
}
```

## algorithms
Algorithms in ADAM are put in folders. Each algorithm folder must have at least the following: (1) a single "run.sh" file, (2) a directory entitled "results", and (3) a "requirements.json" file. How the algorithm runs is completely up to the designer of that algorithm. There are absolutely no limitations on algorithms in ADAM, except for how their input and output look. Input to the "run.sh" file is very simple: argument 1 is the universal path to the dataset folder, and argument 2 is the parameters dictionary given to the algorithm. The output  of "run.sh" (passed back to the mother script with STDOUT) must be parsable json. Output json must contain at least 2 keys: First, "status", which is a flag about whether the algorithm ran normally or threw an error -- "success" in this field represents an error-free process; "fail" or any other string signifies that something went wrong. Second, "output", which contains a string of the name of the output file stored in this algorithm's "results" folder.

### run.sh

An example algorithm's run script might look like this:
```bash
#!/bin/bash

DATASET=$1 # retrieve argument 1
PARAMETERS=$2 # retrieve argument 2
OUTPUT_FILE="res.csv" # here's where we'll save the predicted data

# Note that anything printed in the run.sh script must always be printed to STDERR (i.e., using
# ">&2"), because STDOUT is reserved for our final JSON output. It is recommended to have "run.
# sh" completely silent (no output besides the unprinted json output), but the following line is
# how a message could be printed to be seen while running our mother script.
echo "Running!" >&2

# It's a good idea to find the path the algorithm is stored in
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# It's recommended to create your own environments (in this case, a python env) to make sure 
# dependencies aren't an issue. Here, our algorithm has an environment called ".env" and we are
# accessing the python version inside that environment. These environments should always be
# stored in the algorithm's main folder.
# Our dataset abosolute path, parameters, and our output file name are all passed into our
# algorithm script (in this case, we've set up -d, -p, and -o flags in our python script, but
# the exact implementation of how these values are passed into the script are up to the
# algorithm creator)
"$SCRIPT_DIR/.env/bin/python" $SCRIPT_DIR/alg1.py \
    -d "$DATASET" \
    -p "$PARAMETERS" \
    -o "$SCRIPT_DIR/results/$OUTPUT_FILE" >&2

# After we let the script do its thing, we expect the output file to be populated with its
# predictions. If you'd like to check on that output, you could do that here

# It's recommended to pass any errors that occurred back to the mother script (ADAM/main.py
# rather than handling them in "run.sh".
STATUS=$? # Gets the exit code of the most recent command
# If the exit code of our python program wasn't 0, we'll return an error -- this error is
# handled by the mother script
if [ $STATUS -ne 0 ]; then
    exit $STATUS
fi

# Output to stdout to return the metadata required
echo "{\"status\": \"success\", \"output\": \"$OUTPUT_FILE\"}"
```

### requirements.json

As for the "requirements.json" file, all algorithms must specify for the mother script exactly what they require to be provided in the "parameters" dictionary given. These requirements are simple lists of keys (e.g., I'd like to provide a number of hidden layers to put in my neural net rather than having them hard_coded in somewhere else). These keys must appear in the "parameters" object passed into the algorithm. If an algorithm is not given all the required keys, the mother script will throw an error. Examples of requirements are shown below.

**Example 1**: In the following requirements.json file, we can see that anyone who wants to run this algorithm must provide at least "hidden_layer_count", "learning_rate", and "optimizer" keys in the parameters object. If these keys are not provided, the mother script will throw an error.
```json
["hidden_layer_count", "learning_rate", "optimizer"]
```

**Example 2**: This is an example of an INVALID requirements.json file. Although this is a valid list in json (meaning, there is no Syntax error), since dictionaries in json cannot have non-string type keys, these requirements will never be satisfied. 
```json
[
    1, // INVALID
    2, // INVALID
    "hello",
    "goodbye"
]
```

**Example 3**: If an algorithm requires nothing except the default data provided in the dataset's "data.csv" file, an empty list in requirements.json is appropriate.
```json
[] // this algorithm doesn't need any parameters
```

Keep in mind, extra parameters *not* found in requirements.json are also passed into the algorithm. If a certain parameter is optional, it is not reflected in requirements.json, but in documentation for that algorithm instead. For example, if the neural net were being created in **Example 1**, and we wanted an optional "epochs" key, we could simply put out "epochs" key in the configuration file (in the parameters for this algorithm), and pass the algorithm the value we'd like to use. Designers of algorithms should be advised, however, that since the presence of these parameters is not guaranteed, the algorithm is in charge of checking for their presence, and setting default values for them where needed.


