import sys
import reverse
import uppercase
import lowercase
import spongebob
import length
import scramble

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python cli.py <command> <string>')
        sys.exit(1)

    command = sys.argv[1]
    input_string = ' '.join(sys.argv[2:])

    if command == 'reverse':
        print(reverse.reverse_string(input_string))
    elif command == 'uppercase':
        print(uppercase.uppercase_string(input_string))
    elif command == 'lowercase':
        print(lowercase.lowercase_string(input_string))
    elif command == 'spongebob':
        print(spongebob.spongebob_string(input_string))
    elif command == 'length':
        print(length.string_length(input_string))
    elif command == 'scramble':
        print(scramble.scramble_string(input_string))
    else:
        print(f'Unknown command: {command}')