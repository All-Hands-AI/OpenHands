import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as path from 'path';

describe('OpenHands Resolver Workflow Tests', () => {
  const workflowPath = path.join(__dirname, '../../../openhands/resolver/examples/openhands-resolver.yml');
  let workflowContent: any;

  beforeAll(() => {
    const fileContent = fs.readFileSync(workflowPath, 'utf8');
    workflowContent = yaml.load(fileContent);
  });

  test('workflow file exists and is valid YAML', () => {
    expect(workflowContent).toBeDefined();
    expect(typeof workflowContent).toBe('object');
  });

  test('workflow has correct name', () => {
    expect(workflowContent.name).toBe('Resolve Issue with OpenHands');
  });

  test('workflow has correct event triggers', () => {
    expect(workflowContent.on).toEqual({
      issues: {
        types: ['labeled']
      },
      pull_request: {
        types: ['labeled']
      },
      issue_comment: {
        types: ['created']
      },
      pull_request_review_comment: {
        types: ['created']
      },
      pull_request_review: {
        types: ['submitted']
      }
    });
  });

  test('workflow has required permissions', () => {
    expect(workflowContent.permissions).toEqual({
      contents: 'write',
      'pull-requests': 'write',
      issues: 'write'
    });
  });

  test('workflow has correct job configuration', () => {
    const job = workflowContent.jobs['call-openhands-resolver'];
    expect(job).toBeDefined();
    expect(job.uses).toBe('All-Hands-AI/OpenHands/.github/workflows/openhands-resolver.yml@main');
    
    // Check inputs
    expect(job.with).toEqual({
      macro: '${{ vars.OPENHANDS_MACRO || \'@openhands-agent\' }}',
      max_iterations: '${{ vars.OPENHANDS_MAX_ITER || 50 }}'
    });

    // Check secrets
    expect(job.secrets).toEqual({
      PAT_TOKEN: '${{ secrets.PAT_TOKEN }}',
      PAT_USERNAME: '${{ secrets.PAT_USERNAME }}',
      LLM_MODEL: '${{ secrets.LLM_MODEL }}',
      LLM_API_KEY: '${{ secrets.LLM_API_KEY }}',
      LLM_BASE_URL: '${{ secrets.LLM_BASE_URL }}'
    });
  });

  test('workflow has all required secrets defined', () => {
    const job = workflowContent.jobs['call-openhands-resolver'];
    const requiredSecrets = [
      'PAT_TOKEN',
      'PAT_USERNAME',
      'LLM_MODEL',
      'LLM_API_KEY',
      'LLM_BASE_URL'
    ];

    requiredSecrets.forEach(secret => {
      expect(job.secrets[secret]).toBeDefined();
    });
  });

  test('workflow has valid input variables', () => {
    const job = workflowContent.jobs['call-openhands-resolver'];
    expect(job.with.macro).toMatch(/\$\{\{.*OPENHANDS_MACRO.*\}\}/);
    expect(job.with.max_iterations).toMatch(/\$\{\{.*OPENHANDS_MAX_ITER.*\}\}/);
  });
});
