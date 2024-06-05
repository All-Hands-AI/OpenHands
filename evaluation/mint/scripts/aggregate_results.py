import argparse
import json

# Create the parser
parser = argparse.ArgumentParser(
    description='Calculate the percentage of correct answers in a JSONL file.'
)

# Add the arguments
parser.add_argument(
    'FilePath', metavar='filepath', type=str, help='the path to the JSONL file'
)

# Parse the arguments
args = parser.parse_args()

# Open the JSONL file
with open(args.FilePath, 'r') as f:
    lines = f.readlines()

# Initialize the count of total and correct answers
total = len(lines)
correct = 0

# Iterate over the lines in the file
for line in lines:
    # Parse the line as JSON
    data = json.loads(line)

    # If the test result is true, increment the count of correct answers
    if data['test_result']:
        correct += 1

# Calculate the percentage of correct answers
percentage_correct = (correct / total) * 100

print(f'Percentage of correct answers: {percentage_correct}%')
