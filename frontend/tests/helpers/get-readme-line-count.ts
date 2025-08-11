import { execSync } from 'child_process';

export function getReadmeLineCount(): number {
  try {
    const output = execSync('wc -l ../../../README.md').toString().trim();
    const lineCount = parseInt(output.split(' ')[0]);
    return lineCount;
  } catch (error) {
    console.error('Error getting README.md line count:', error);
    return -1;
  }
}
