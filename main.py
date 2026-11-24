# ignore warnings
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from pathlib import Path
import argparse
import json
import subprocess
import threading

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

DATASETS_FOLDER = Path("/Users/a02523625/Documents/HorsburghRA/11_26/ADAM/datasets")
DATASET_MAIN_FILE = "data.csv"
REQUIRED_DATASET_FILES = [DATASET_MAIN_FILE]
REQUIRED_DATA_COLUMNS = ["timestamp", "value", "label"]

ALGORITHMS_FOLDER = Path("./algorithms")
ALGORITHM_RUN_NAME = "run.sh"
ALGORITHM_REQUIREMENTS_NAME = "requirements.json"
ALGORITHMS_RESULTS_FOLDER = "results"
REQUIRED_ALGORITHM_FILES = [ALGORITHM_RUN_NAME, ALGORITHM_REQUIREMENTS_NAME]
REQUIRED_ALGORITHM_DIRECTORIES = [ALGORITHMS_RESULTS_FOLDER]

OUTPUT_STATUS_KEY = "status"
OUTPUT_FILE_KEY = "output"
REQUIRED_OUTPUT_KEYS = [OUTPUT_STATUS_KEY, OUTPUT_FILE_KEY]

CONFIGS_FOLDER = Path("./configs")
CONFIG_KEYS = ["dataset_name", "algorithm_name", "parameters"]


class Configuration:
    def __init__(self, config_name):
        self.config_name = config_name

    def parse_config(self):
        if not (CONFIGS_FOLDER / self.config_name).is_file():
            raise ValueError(f"Could not find '{self.config_name}' in the '{CONFIGS_FOLDER}' folder!")

        config = json.load(open(CONFIGS_FOLDER / self.config_name, "r"))

        for key in config.keys():
            if key not in CONFIG_KEYS:
                raise ValueError(f"Key '{key}' is not permitted in the '{CONFIGS_FOLDER / self.config_name}' file! Valid keys are: {CONFIG_KEYS}; All extra data should be stored in the 'parameters' key.")

        dataset_names = config.get("dataset_name")
        algorithm_names = config.get("algorithm_name")
        parameters = config.get("parameters")
        if dataset_names is None or algorithm_names is None or parameters is None:
            raise ValueError(f"One or more required keys are missing from the '{CONFIGS_FOLDER / self.config_name}' file! Required keys are: {CONFIG_KEYS}")

        # check if we got multiple algorithms and parameters, and if so, ensure they are lists of the same length
        if isinstance(algorithm_names, list) and isinstance(parameters, list):
            if len(algorithm_names) != len(parameters):
                raise ValueError(f"Length of 'algorithm_names' and 'parameters' lists must be the same in the '{CONFIGS_FOLDER / self.config_name}' file!")

        # if they aren't already lists, convert them to lists for consistency
        if not isinstance(dataset_names, list): dataset_names = [dataset_names]
        if not isinstance(algorithm_names, list): algorithm_names = [algorithm_names]
        if not isinstance(parameters, list): parameters = [parameters]

        # make sure all of the entries in dataset_names and algorithm_names are strings
        for dn in dataset_names:
            if not isinstance(dn, str): raise ValueError(f"Not all datasets passed in are findable! Make sure datasets are represented using strings.")
        for an in algorithm_names:
            if not isinstance(an, str): raise ValueError(f"Not all algorithms passed in are findable! Make sure algorithms are represented using strings.")

        return dataset_names, algorithm_names, parameters


class Dataset:
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name
        self.validate()

    def validate(self):
        if not (DATASETS_FOLDER / self.dataset_name).is_dir():
            raise ValueError(f"Could not find '{self.dataset_name}' in the '{DATASETS_FOLDER}' folder!")

        for file in REQUIRED_DATASET_FILES:
            if not (DATASETS_FOLDER / self.dataset_name / file).is_file():
                raise ValueError(f"Could not find '{file}' in the '{DATASETS_FOLDER / self.dataset_name}' folder!")

        try:
            df = pd.read_csv(self.get_main_data_filepath())
        except Exception:
            raise ValueError(f"Unable to parse '{self.get_main_data_filepath()}' into a pandas dataframe!")
        for col in REQUIRED_DATA_COLUMNS:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' is missing from the '{self.get_main_data_filepath()}' file!")

    def get_main_data_filepath(self):
        return DATASETS_FOLDER / self.dataset_name / DATASET_MAIN_FILE


class Algorithm:
    def __init__(self, algorithm_name, parameters):
        self.algorithm_name = algorithm_name
        self.parameters = parameters
        self.validate()

    def validate(self):
        if not (ALGORITHMS_FOLDER / self.algorithm_name).is_dir():
            raise ValueError(f"Could not find '{self.algorithm_name}' in the '{ALGORITHMS_FOLDER}' folder!")

        for file in REQUIRED_ALGORITHM_FILES:
            if not (ALGORITHMS_FOLDER / self.algorithm_name / file).is_file():
                raise ValueError(f"Could not find file: '{file}' in the '{ALGORITHMS_FOLDER / self.algorithm_name}' folder!")

        for dir in REQUIRED_ALGORITHM_DIRECTORIES:
            if not (ALGORITHMS_FOLDER / self.algorithm_name / dir).is_dir():
                raise ValueError(f"Could not find directory: '{dir}' in the '{ALGORITHMS_FOLDER / self.algorithm_name}' folder!")

        if not isinstance(self.parameters, dict):
            raise ValueError(f"Parameters passed into '{self.algorithm_name}' are of type {type(self.parameters)} instead of {type({})}")

        self.validate_requirements()

    def validate_requirements(self):
        reqs = json.load(open(ALGORITHMS_FOLDER / self.algorithm_name / ALGORITHM_REQUIREMENTS_NAME, "r"))

        for req in reqs:
            if req not in self.parameters:
                raise ValueError(f"Could not find required key '{req}' in parameters given to '{self.algorithm_name}'!")

    def run(self, dataset: Dataset):
        run_script_path = ALGORITHMS_FOLDER / self.algorithm_name / ALGORITHM_RUN_NAME

        def read_stderr(process):
            for line in process.stderr:
                print(f"{line}", end="")

        start_time = pd.Timestamp.now()
        print(f"{BLUE}>>> Start: {self.algorithm_name} / {dataset.dataset_name} > {start_time}{RESET}")
        process = subprocess.Popen(
            [run_script_path, DATASETS_FOLDER / dataset.dataset_name, json.dumps(parameters)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Read progress in a separate thread
        thread = threading.Thread(target=read_stderr, args=(process,))
        thread.start()

        # Read final metadata
        output = process.stdout.read()

        thread.join()
        return_code = process.wait()

        end_time = pd.Timestamp.now()
        duration_string = str(end_time - start_time).replace('0 days ', '')

        def abort():
            print(f"{BLUE}>>> Exitting...{RESET}")
            return {OUTPUT_STATUS_KEY: "fail", OUTPUT_FILE_KEY: None}

        if return_code != 0:
            print(f"{RED}ERROR: '{self.algorithm_name}' failed [Return code: {return_code}]{RESET}")
            return abort()

        try:
            metadata = json.loads(output)
        except Exception:
            print(f"{RED}ERROR: '{self.algorithm_name}' failed to return valid json output to stdout. {RESET}")
            return abort()
        for key in REQUIRED_OUTPUT_KEYS:
            if key not in metadata:
                print(f"{RED}ERROR: '{self.algorithm_name}' failed to return with valid output! Required key '{key}' was not found in output of '{self.algorithm_name}' {RESET}")
                return abort()

        print(f"{BLUE}>>> Completed. Duration: {duration_string}{RESET}")
        return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="The name of the configuration to use")
    args = parser.parse_args()

    if args.config is None:
        args.config = input("Enter configuration name: ")

    args.config += '.json' if not args.config.endswith('.json') else ''

    print(f"{BLUE}>>> Parsing and Validating Inputs...{RESET}")

    config = Configuration(args.config)
    dataset_names, algorithm_names, parameters = config.parse_config()

    datasets = [Dataset(dataset_name) for dataset_name in dataset_names]
    algorithms = [Algorithm(algorithm_name, parameters[ind]) for ind, algorithm_name in enumerate(algorithm_names)]

    outputs = []
    for algorithm in algorithms:
        for dataset in datasets:
            outputs.append({
                "dataset_used": dataset.dataset_name,
                "algorithm_used": algorithm.algorithm_name,
                "parameters_used": algorithm.parameters,
                "output": algorithm.run(dataset)
            })

    print(json.dumps(outputs, indent=2))
