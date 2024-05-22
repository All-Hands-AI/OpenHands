import os

from opendevin.llm import readers

files_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'multi_modal_files'
)


def test_txt_reader():
    reader = readers.TXTReader()

    utf8_file_path = os.path.join(files_dir, 'utf8.txt')
    with open(utf8_file_path, 'r', encoding='utf-8') as file:
        assert reader.parse(utf8_file_path) == file.read()

    utf16_file_path = os.path.join(files_dir, 'utf16.txt')
    with open(utf16_file_path, 'r', encoding='utf-16-be') as file:
        assert reader.parse(utf16_file_path) == file.read()
