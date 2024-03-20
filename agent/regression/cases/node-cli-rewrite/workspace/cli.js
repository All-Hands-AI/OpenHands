const process = require('process');
const commands = require('./commands');

function printHelp() {
  const helpText = `
Usage: node cli.js <command> <string>

Commands:
    reverse - Reverses the input string.
    uppercase - Converts the input string to uppercase.
    lowercase - Converts the input string to lowercase.
    spongebob - Converts the input string to spongebob case.
    length - Returns the length of the input string.
    scramble - Randomly scrambles the characters in the input string.
`;
  console.log(helpText);
}

if (process.argv.length === 3 && process.argv[2] === '--help') {
  printHelp();
  process.exit(0);
} else if (process.argv.length < 4) {
  console.log('Usage: node cli.js <command> <string>');
  process.exit(1);
}

const command = process.argv[2];
const inputString = process.argv[3];

if (command in commands) {
  console.log(commands[command](inputString));
} else {
  console.log('Invalid command!');
}