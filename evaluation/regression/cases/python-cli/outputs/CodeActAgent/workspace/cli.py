import sys
from reverse import reverse_string
from uppercase import to_uppercase
from lowercase import to_lowercase
from spongebob import to_spongebob
from length import string_length
from scramble import scramble_string

def main():
    if len(sys.argv) < 3:
        print('Usage: python cli.py <command> <string>')
        sys.exit(1)

    command = sys.argv[1]
    input_string = ' '.join(sys.argv[2:])

    if command == 'reverse':
        print(reverse_string(input_string))
    elif command == 'uppercase':
        print(to_uppercase(input_string))
    elif command == 'lowercase':
        print(to_lowercase(input_string))
    elif command == 'spongebob':
        print(to_spongebob(input_string))
    elif command == 'length':
        print(string_length(input_string))
    elif command == 'scramble':
        print(scramble_string(input_string))
    else:
        print('Invalid command. Available commands: reverse, uppercase, lowercase, spongebob, length, scramble')

if __name__ == '__main__':
    main()
