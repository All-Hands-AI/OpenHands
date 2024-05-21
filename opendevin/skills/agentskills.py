import os

CURRENT_FILE = None
CURRENT_LINE = 1
WINDOW = 10

def open_file(path, line_number=None):
    global CURRENT_FILE, CURRENT_LINE
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File {path} not found")
    
    CURRENT_FILE = path
    total_lines = sum(1 for _ in open(CURRENT_FILE))
    
    if line_number is not None:
        if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
            raise ValueError(f"Line number must be between 1 and {total_lines}")
        CURRENT_LINE = line_number
    else:
        CURRENT_LINE = 1
    
    print(f"[File: {os.path.abspath(CURRENT_FILE)} ({total_lines} lines total)]")
    _print_window()

def _print_window():
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    with open(CURRENT_FILE, 'r') as file:
        lines = file.readlines()
        start = max(0, CURRENT_LINE - WINDOW // 2)
        end = min(len(lines), CURRENT_LINE + WINDOW // 2)
        for i in range(start, end):
            print(f"{i + 1}: {lines[i].strip()}")

def goto_line(line_number):
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError("No file open. Use the open_file function first.")
    
    total_lines = sum(1 for _ in open(CURRENT_FILE))
    if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
        raise ValueError(f"Line number must be between 1 and {total_lines}")
    
    CURRENT_LINE = line_number
    _print_window()

def scroll_down():
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError("No file open. Use the open_file function first.")
    
    total_lines = sum(1 for _ in open(CURRENT_FILE))
    CURRENT_LINE = min(CURRENT_LINE + WINDOW, total_lines)
    _print_window()

def scroll_up():
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError("No file open. Use the open_file function first.")
    
    CURRENT_LINE = max(CURRENT_LINE - WINDOW, 1)
    _print_window()

def create_file(filename):
    global CURRENT_FILE, CURRENT_LINE
    if os.path.exists(filename):
        raise FileExistsError(f"File '{filename}' already exists.")
    
    with open(filename, 'w') as file:
        file.write("\n")
    
    open_file(filename)

def submit():
    import subprocess
    import shutil

    root_dir = os.getenv('ROOT', '/workspace')
    swe_cmd_work_dir = os.getenv('SWE_CMD_WORK_DIR', '/workspace')

    os.chdir(root_dir)

    patch_file = os.path.join(swe_cmd_work_dir, 'test.patch')
    if os.path.exists(patch_file) and os.path.getsize(patch_file) > 0:
        subprocess.run(['git', 'apply', '-R', patch_file], check=True)

    subprocess.run(['git', 'add', '-A'], check=True)
    with open('model.patch', 'w') as patch:
        subprocess.run(['git', 'diff', '--cached'], stdout=patch, check=True)

    with open('model.patch', 'r') as patch:
        print("<<SUBMISSION||")
        print(patch.read())
        print("||SUBMISSION>>")

def search_dir(search_term, dir_path='./'):
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"Directory {dir_path} not found")
    
    matches = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            with open(file_path, 'r', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_term in line:
                        matches.append((file_path, line_num, line.strip()))
    
    if not matches:
        print(f"No matches found for \"{search_term}\" in {dir_path}")
        return
    
    num_matches = len(matches)
    num_files = len(set(match[0] for match in matches))
    
    if num_files > 100:
        print(f"More than {num_files} files matched for \"{search_term}\" in {dir_path}. Please narrow your search.")
        return
    
    print(f"Found {num_matches} matches for \"{search_term}\" in {dir_path}:")
    for file_path, line_num, line in matches:
        print(f"{file_path} (Line {line_num}): {line}")
    print(f"End of matches for \"{search_term}\" in {dir_path}")
    for match in matches:
        print(match)

def search_file(search_term, file_path=None):
    global CURRENT_FILE
    if file_path is None:
        if CURRENT_FILE is None:
            raise FileNotFoundError("No file open. Use the open_file function first.")
        file_path = CURRENT_FILE
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File {file_path} not found")
    
    matches = []
    with open(file_path, 'r', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            if search_term in line:
                matches.append((line_num, line.strip()))
    
    if not matches:
        print(f"No matches found for \"{search_term}\" in {file_path}")
        return
    
    num_matches = len(matches)
    num_lines = len(set(match[0] for match in matches))
    
    if num_lines > 100:
        print(f"More than {num_lines} lines matched for \"{search_term}\" in {file_path}. Please narrow your search.")
        return
    
    print(f"Found {num_matches} matches for \"{search_term}\" in {file_path}:")
    for line_num, line in matches:
        print(f"Line {line_num}: {line}")

def find_file(file_name, dir_path='./'):
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"Directory {dir_path} not found")
    
    matches = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file == file_name:
                matches.append(os.path.join(root, file))
    
    if not matches:
        print(f"No matches found for \"{file_name}\" in {dir_path}")
        return
    
    num_matches = len(matches)
    print(f"Found {num_matches} matches for \"{file_name}\" in {dir_path}:")
    for match in matches:
        print(match)
