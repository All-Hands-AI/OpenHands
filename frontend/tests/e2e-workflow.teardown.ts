import { FullConfig } from '@playwright/test';
import { execSync } from 'child_process';

async function globalTeardown(config: FullConfig) {
  console.log('Stopping OpenHands application...');

  try {
    // Find and kill the OpenHands processes
    execSync('pkill -f "make run" || true');
    execSync('pkill -f "python -m openhands" || true');

    console.log('OpenHands application stopped successfully.');
  } catch (error) {
    console.error('Failed to stop OpenHands application:', error);
  }
}

export default globalTeardown;
