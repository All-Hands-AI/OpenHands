import { FullConfig } from '@playwright/test';
import { execSync } from 'child_process';

async function globalSetup(config: FullConfig) {
  console.log('Starting OpenHands application for end-to-end testing...');

  try {
    // Start OpenHands in the background and redirect output to a log file
    execSync('cd ../.. && export INSTALL_DOCKER=0 export RUNTIME=local && make build && make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0 &> /tmp/openhands-e2e-test.log &', {
      stdio: 'inherit'
    });

    // Wait for the application to start
    console.log('Waiting for OpenHands to start...');
    await new Promise(resolve => setTimeout(resolve, 30000));

    console.log('OpenHands application started successfully.');
  } catch (error) {
    console.error('Failed to start OpenHands application:', error);
    process.exit(1);
  }
}

export default globalSetup;
