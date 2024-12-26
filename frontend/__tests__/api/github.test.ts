import { describe, expect, it, vi } from 'vitest';
import { github } from '../../src/api/github-axios-instance';
import { retrieveLatestGitHubCommit } from '../../src/api/github';

vi.mock('../../src/api/github-axios-instance', () => ({
  github: {
    get: vi.fn(),
  },
}));

describe('retrieveLatestGitHubCommit', () => {
  it('should return the latest commit when repository has commits', async () => {
    const mockCommit = {
      sha: '123abc',
      commit: {
        message: 'Initial commit',
      },
    };

    (github.get as any).mockResolvedValueOnce({
      data: [mockCommit],
    });

    const result = await retrieveLatestGitHubCommit('user/repo');
    expect(result).toEqual(mockCommit);
  });

  it('should return null when repository is empty', async () => {
    const error = new Error('Repository is empty');
    (error as any).response = { status: 409 };
    (github.get as any).mockRejectedValueOnce(error);

    const result = await retrieveLatestGitHubCommit('user/empty-repo');
    expect(result).toBeNull();
  });

  it('should throw error for other error cases', async () => {
    const error = new Error('Network error');
    (error as any).response = { status: 500 };
    (github.get as any).mockRejectedValueOnce(error);

    await expect(retrieveLatestGitHubCommit('user/repo')).rejects.toThrow();
  });
});
