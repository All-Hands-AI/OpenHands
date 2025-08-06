import { test, expect } from '@playwright/test';
import { getReadmeLineCount } from './helpers/get-readme-line-count';

test('OpenHands end-to-end workflow', async ({ page }) => {
  // Navigate to the OpenHands application
  await page.goto('/');

  // Wait for the repository selection dropdown to be visible
  await page.waitForSelector('button:has-text("Select a repository")');

  // Click on the repository selection dropdown
  await page.click('button:has-text("Select a repository")');

  // Wait for the dropdown to open and select the OpenHands repository
  await page.waitForSelector('div[role="option"]:has-text("All-Hands-AI/OpenHands")');
  await page.click('div[role="option"]:has-text("All-Hands-AI/OpenHands")');

  // Click the Launch button
  await page.waitForSelector('button:has-text("Launch")');
  await page.click('button:has-text("Launch")');

  // Check that the interface changes to the agent control interface
  await page.waitForSelector('div:has-text("Connecting")', { state: 'visible' });

  // Check that we go through the "Initializing Agent" state
  await page.waitForSelector('div:has-text("Initializing Agent")', { state: 'visible' });

  // Check that we reach the "Agent is waiting for user input..." state
  await page.waitForSelector('div:has-text("Agent is waiting for user input...")', { state: 'visible', timeout: 60000 });

  // Enter the test question and submit
  await page.fill('textarea[placeholder="Message OpenHands..."]', 'How many lines are there in the main README.md file?');
  await page.click('button[aria-label="Send message"]');

  // Check that we go through the "Agent is running task" state
  await page.waitForSelector('div:has-text("Agent is running task")', { state: 'visible' });

  // Check that we reach the "Agent has finished the task." state
  await page.waitForSelector('div:has-text("Agent has finished the task.")', { state: 'visible', timeout: 120000 });

  // Get the final agent message
  const finalMessage = await page.locator('.message-content').last().textContent();

  // Get the actual line count of README.md
  const readmeLineCount = getReadmeLineCount();

  // Check that the final message contains the correct line count
  expect(finalMessage).toContain(readmeLineCount.toString());
});
