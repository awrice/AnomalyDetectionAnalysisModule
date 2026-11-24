from pathlib import Path
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dataset", help="The name of the dataset to use")
parser.add_argument("-p", "--parameters", help="All the parameters needed to make this algorithm work")
parser.add_argument("-o", "--output", help="The name of the output file to use")
args = parser.parse_args()

# Here's our parameters
print("DS: " + args.dataset)
print("PARAMS: " + str(args.parameters))
print("OUTPUT: " + args.output)

# the dataset always has a data.csv file in it.
data_path = Path(args.dataset) / "data.csv"

# Read the csv given and take the columns we know we have (other columns might be specified as safe to access in the parameters argument)
df = pd.read_csv(data_path)[["timestamp", "value"]]

# Our predicted value is a simple cutoff
df["predicted"] = (df['value'] > 11).astype(int)

# export the prediction to our output provided to the file
df.to_csv(args.output)