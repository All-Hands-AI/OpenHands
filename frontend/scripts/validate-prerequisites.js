
const execSync = require('child_process').execSync;

const prerequisites = [
  { name: 'NodeJS', command: 'node --version', expectedVersion: 'v18.17.1' },
  { name: 'Python', command: 'python --version', expectedVersion: 'Python 3.11' },
  { name: 'Docker', command: 'docker --version', expectedVersion: 'Docker version 23.01.0' },
  { name: 'Poetry', command: 'poetry --version', expectedVersion: 'Poetry version 1.8' }
];

function executeCommand(command) {
  try {
    return execSync(command).toString().trim();
  } catch (error) {
    console.error(`${command} failed to execute`);
    process.exit(1);
  }
}

function validatePrerequisites() {
  prerequisites.forEach(prerequisite => {
    console.log(`Checking installation of ${prerequisite.name}...`);
    const output = executeCommand(prerequisite.command);
    if (!output.includes(prerequisite.expectedVersion)) {
      console.error(`Validation failed for ${prerequisite.name}. Expected: ${prerequisite.expectedVersion}, Found: ${output}`);
      process.exit(1);
    }
    console.log(`${prerequisite.name} is correctly installed.`);
  });
  console.log('All prerequisites are correctly installed.');
}

validatePrerequisites();
