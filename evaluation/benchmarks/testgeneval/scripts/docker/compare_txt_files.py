def print_diff_ignore_order(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        file1_lines = set(f1.readlines())
        file2_lines = set(f2.readlines())

    only_in_file1 = file1_lines - file2_lines
    only_in_file2 = file2_lines - file1_lines

    if only_in_file1:
        print(f'Lines in {file1} but not in {file2}:')
        for line in sorted(only_in_file1):
            print(f'- {line.strip()}')

    # if only_in_file2:
    #     print(f"Lines in {file2} but not in {file1}:")
    #     for line in sorted(only_in_file2):
    #         print(f"+ {line.strip()}")

    if not only_in_file1 and not only_in_file2:
        print('The files have the same content (ignoring line order).')


if __name__ == '__main__':
    # Usage
    lite1 = 'all-swebench-lite-instance-images.txt'  # Replace with the path to your first file
    lite2 = '../../swe_bench/scripts/docker/all-swebench-lite-instance-images.txt'  # Replace with the path to your second file
    print_diff_ignore_order(lite1, lite2)

    full1 = 'all-swebench-full-instance-images.txt'  # Replace with the path to your first file
    full2 = '../../swe_bench/scripts/docker/all-swebench-full-instance-images.txt'  # Replace with the path to your second file
    print_diff_ignore_order(full1, full2)
