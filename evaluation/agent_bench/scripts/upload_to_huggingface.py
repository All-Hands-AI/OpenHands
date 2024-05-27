import argparse

from datasets import Dataset, DatasetDict


def main(username, dataset_name, csv_file_path):
    test_dataset = Dataset.from_csv(csv_file_path)
    dataset_dict = DatasetDict({'test': test_dataset})

    dataset_dict.push_to_hub(f'{username}/{dataset_name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Upload a CSV file to Hugging Face datasets'
    )
    parser.add_argument(
        '--username', type=str, required=True, help='Your Hugging Face username'
    )
    parser.add_argument(
        '--dataset_name', type=str, required=True, help='The name of the dataset'
    )
    parser.add_argument(
        '--csv_file_path', type=str, required=True, help='The path to the CSV file'
    )

    args = parser.parse_args()

    main(args.username, args.dataset_name, args.csv_file_path)
