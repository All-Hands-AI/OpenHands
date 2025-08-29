import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useGitRepositories } from './use-git-repositories';

// Mock the OpenHands API module
vi.mock('../../api/open-hands', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    retrieveInstallationRepositories: vi.fn(),
  };
});

// Mock the utils module
vi.mock('../../utils/utils', () => ({
  shouldUseInstallationRepos: vi.fn(() => true),
}));

// Mock the user providers hook
vi.mock('../use-user-providers', () => ({
  useUserProviders: vi.fn(() => ({
    providers: ['github'], // Mock that github provider is available
  })),
}));

// Mock the config hook
vi.mock('./use-config', () => ({
  useConfig: vi.fn(() => ({
    data: { APP_MODE: 'saas' }, // Mock SaaS mode
  })),
}));

import { retrieveInstallationRepositories } from '../../api/open-hands';

describe('useGitRepositories - Real Environment Bug Reproduction', () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: ReactNode }) => JSX.Element;
  const mockRetrieveInstallationRepositories = retrieveInstallationRepositories as any;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    vi.clearAllMocks();
  });

  it('should reproduce the infinite pagination loop bug with real hook', async () => {
    // Track all API calls to see the bug
    const apiCallLog: Array<{
      installationIndex: number;
      installationId: string;
      repoPage: number;
      timestamp: number;
    }> = [];

    // Mock the same installations as browser
    const mockInstallations = ['57992165', '63523234'];

    // Mock API responses exactly like our browser mocks
    mockRetrieveInstallationRepositories.mockImplementation(
      async (provider: string, installationIndex: number, installations: string[], page: number) => {
        const installationId = installations[installationIndex];
        const callInfo = {
          installationIndex,
          installationId,
          repoPage: page,
          timestamp: Date.now(),
        };
        apiCallLog.push(callInfo);

        console.log('🧪 TEST: MOCK API CALL -', callInfo);

        // Return different responses based on installation index
        if (installationIndex === 0) {
          // Return repos for installation 0 (same as browser mock)
          return {
            data: [
              { id: 1, full_name: 'org1/repo1', link_header: '' },
              { id: 2, full_name: 'org1/repo2', link_header: '' },
            ],
            nextPage: null, // No more pages for this installation
            installationIndex: 1, // Should move to installation 1
          };
        } else if (installationIndex === 1) {
          // Return repos for installation 1 (same as browser mock)
          return {
            data: [
              { id: 3, full_name: 'org2/repo3', link_header: '' },
              { id: 4, full_name: 'org2/repo4', link_header: '' },
              { id: 5, full_name: 'org2/repo5', link_header: '' },
            ],
            nextPage: null, // No more pages
            installationIndex: null, // No more installations
          };
        } else {
          throw new Error(`Unexpected installation index: ${installationIndex}`);
        }
      }
    );

    // Verify our mock is set up correctly
    console.log('🧪 TEST: Mock function type:', typeof mockRetrieveInstallationRepositories);
    console.log('🧪 TEST: Mock function calls before test:', mockRetrieveInstallationRepositories.mock?.calls?.length || 0);

    console.log('🧪 TEST: Starting hook with installations:', mockInstallations);

    // Render the actual hook with same parameters as browser
    const { result } = renderHook(
      () =>
        useGitRepositories({
          provider: 'github',
          installations: mockInstallations,
          enabled: true, // Explicitly enable the hook
        }),
      { wrapper }
    );

    console.log('🧪 TEST: Hook rendered, waiting for initial load...');

    // Wait for initial load (installation 0)
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    }, { timeout: 10000 });

    console.log('🧪 TEST: Initial load complete. Hook state:', {
      isLoading: result.current.isLoading,
      isError: result.current.isError,
      error: result.current.error?.message,
      hasNextPage: result.current.hasNextPage,
      isFetchingNextPage: result.current.isFetchingNextPage,
      dataPages: result.current.data?.pages?.length,
    });

    // Get all repositories loaded so far
    const allRepos = result.current.data?.pages?.flatMap(page => page.data) || [];
    console.log('🧪 TEST: Repositories loaded:', allRepos.map(r => r.full_name));
    console.log('🧪 TEST: API calls made so far:', apiCallLog.length);

    // If there's a next page, try to fetch it manually
    if (result.current.hasNextPage && result.current.fetchNextPage) {
      console.log('🧪 TEST: Has next page, attempting to fetch...');

      // Set a timeout to detect infinite loop
      const fetchPromise = result.current.fetchNextPage();
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Fetch timeout - possible infinite loop')), 5000)
      );

      try {
        await Promise.race([fetchPromise, timeoutPromise]);

        // Wait for fetch to complete
        await waitFor(() => {
          expect(result.current.isFetchingNextPage).toBe(false);
        }, { timeout: 5000 });

        console.log('🧪 TEST: Fetch completed successfully');
      } catch (error) {
        console.log('🧪 TEST: Fetch failed or timed out:', error);
      }
    } else {
      console.log('🧪 TEST: No next page available');
    }

    // Final state
    const finalRepos = result.current.data?.pages?.flatMap(page => page.data) || [];
    console.log('🧪 TEST: Final repositories:', finalRepos.map(r => r.full_name));
    console.log('🧪 TEST: Final API call log:', apiCallLog);

    // Test expectations - focus on the actual hook behavior
    console.log('🧪 TEST: Running assertions...');

    // The key test: Hook should complete without infinite loop
    // This was the main bug - the hook would get stuck in infinite pagination
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);

    // Hook should have processed both installations (2 pages total)
    expect(result.current.data?.pages).toHaveLength(2);

    // Hook should not have next page when done (no infinite loop)
    expect(result.current.hasNextPage).toBe(false);

    // Hook should not be stuck fetching (no infinite loop)
    expect(result.current.isFetchingNextPage).toBe(false);

    console.log('🧪 TEST: SUCCESS - Hook completed without infinite loop!');
    console.log('🧪 TEST: Pages processed:', result.current.data?.pages?.length);
    console.log('🧪 TEST: Has next page:', result.current.hasNextPage);
    console.log('🧪 TEST: Is fetching next page:', result.current.isFetchingNextPage);
  }, 15000); // Longer timeout for this complex test
});
