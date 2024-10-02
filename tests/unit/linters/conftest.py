import pytest


@pytest.fixture
def syntax_error_py_file(tmp_path):
    file_content = """
    def foo():
        print("Hello, World!")
    print("Wrong indent")
    foo(
    """
    file_path = tmp_path / 'test_file.py'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def wrongly_indented_py_file(tmp_path):
    file_content = """
    def foo():
            print("Hello, World!")
    """
    file_path = tmp_path / 'test_file.py'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def simple_correct_py_file(tmp_path):
    file_content = 'print("Hello, World!")\n'
    file_path = tmp_path / 'test_file.py'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def simple_correct_py_func_def(tmp_path):
    file_content = """def foo():
    print("Hello, World!")
foo()
"""
    file_path = tmp_path / 'test_file.py'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def simple_correct_ruby_file(tmp_path):
    file_content = """def foo
  puts "Hello, World!"
end
foo
"""
    file_path = tmp_path / 'test_file.rb'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def simple_incorrect_ruby_file(tmp_path):
    file_content = """def foo():
    print("Hello, World!")
foo()
"""
    file_path = tmp_path / 'test_file.rb'
    file_path.write_text(file_content)
    return str(file_path)


@pytest.fixture
def parenthesis_incorrect_ruby_file(tmp_path):
    file_content = """def print_hello_world()\n    puts 'Hello World'\n"""
    file_path = tmp_path / 'test_file.rb'
    file_path.write_text(file_content)
    return str(file_path)
