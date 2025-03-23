# React Query to Redux Migration Plan

## Overview

This document outlines the step-by-step plan to migrate all React Query usage in the OpenHands frontend to Redux Toolkit. The migration will involve converting all data fetching and state management from React Query to Redux Toolkit's RTK Query.

## Current State Analysis

The OpenHands frontend currently uses:
- **Redux Toolkit** for UI state management (chat messages, file state, agent state, etc.)
- **React Query** for data fetching and server state management

React Query is primarily used for:
1. API data fetching (configurations, files, user data)
2. Mutations (creating conversations, uploading files, etc.)
3. Caching and invalidation of server data

## Migration Strategy

### Phase 1: Setup RTK Query API Service

1. Create a base API service using RTK Query
2. Configure caching, error handling, and request lifecycle hooks to match current React Query behavior
3. Ensure the API service integrates with the existing Redux store

### Phase 2: Migrate Query Hooks to RTK Query Endpoints

1. Create API slice files for logical groupings of endpoints
2. Convert each React Query hook to an RTK Query endpoint
3. Update the error handling to match the current React Query setup
4. Ensure proper tag-based cache invalidation

### Phase 3: Migrate Mutation Hooks

1. Convert each React Query mutation to an RTK Query mutation
2. Implement proper cache invalidation strategies
3. Ensure error handling matches current behavior

### Phase 4: Update Components

1. Replace all React Query hook usages with RTK Query hooks
2. Update any components that rely on React Query's loading/error states
3. Ensure proper data refetching behavior is maintained

### Phase 5: Clean Up

1. Remove React Query dependencies
2. Remove React Query provider from the application
3. Update tests to use RTK Query instead of React Query
4. Ensure all functionality works as expected

## Detailed Implementation Plan

### Phase 1: Setup RTK Query API Service

1. Create a base API service in `src/api/api-service.ts`
2. Configure the base URL, headers, and error handling
3. Integrate with the existing Redux store in `src/store.ts`

### Phase 2: Migrate Query Hooks

Convert the following query hooks to RTK Query endpoints:

1. **Configuration Endpoints**
   - `useConfig` → `getConfig`
   - `useAIConfigOptions` → `getAIConfigOptions`
   - `useSettings` → `getSettings`

2. **File Management Endpoints**
   - `useListFiles` → `listFiles`
   - `useListFile` → `getFile`

3. **User & Authentication Endpoints**
   - `useIsAuthed` → `getAuthStatus`
   - `useGithubUser` → `getGithubUser`
   - `useUserConversations` → `getUserConversations`
   - `useUserConversation` → `getUserConversation`

4. **GitHub Integration Endpoints**
   - `useAppInstallations` → `getAppInstallations`
   - `useAppRepositories` → `getAppRepositories`
   - `useSearchRepositories` → `searchRepositories`
   - `useUserRepositories` → `getUserRepositories`

5. **Miscellaneous Endpoints**
   - `useActiveHost` → `getActiveHost`
   - `useBalance` → `getBalance`
   - `useConversationConfig` → `getConversationConfig`
   - `useGetPolicy` → `getPolicy`
   - `useGetRiskSeverity` → `getRiskSeverity`
   - `useGetTraces` → `getTraces`
   - `useVSCodeUrl` → `getVSCodeUrl`

### Phase 3: Migrate Mutation Hooks

Convert the following mutation hooks to RTK Query endpoints:

1. **Conversation Management**
   - `useCreateConversation` → `createConversation`
   - `useDeleteConversation` → `deleteConversation`
   - `useUpdateConversation` → `updateConversation`
   - `useGetTrajectory` → `getTrajectory`

2. **File Operations**
   - `useUploadFiles` → `uploadFiles`

3. **User Actions**
   - `useSubmitFeedback` → `submitFeedback`
   - `useSaveSettings` → `saveSettings`
   - `useLogout` → `logout`

4. **Payment Processing**
   - `useCreateStripeCheckoutSession` → `createStripeCheckoutSession`

### Phase 4: Update Components

1. Identify all components using React Query hooks
2. Replace React Query hooks with RTK Query hooks
3. Update loading, error, and data handling patterns
4. Ensure refetching behavior is maintained

### Phase 5: Clean Up

1. Remove React Query provider from `entry.client.tsx`
2. Remove React Query dependencies from `package.json`
3. Update tests to use RTK Query mocks instead of React Query mocks
4. Perform final testing to ensure all functionality works as expected

## Testing Strategy

1. Create unit tests for each new RTK Query endpoint
2. Test cache invalidation behavior
3. Test error handling
4. Test loading states
5. Ensure all components render correctly with the new data fetching approach

## Rollback Plan

If issues arise during the migration:

1. Keep both React Query and RTK Query implementations side by side
2. Implement feature flags to switch between implementations
3. Roll back to React Query if critical issues are discovered

## Progress Update

### Completed Tasks

- ✅ Created base API service using RTK Query
- ✅ Configured the base URL, headers, and error handling
- ✅ Integrated with the existing Redux store
- ✅ Created API slices for different endpoints:
  - Auth API slice
  - Config API slice
  - Files API slice
  - GitHub API slice
  - Settings API slice
  - Billing API slice
  - Misc API slice
- ✅ Created custom hooks that use RTK Query:
  - useConfig
  - useListFiles
  - useListFile
  - useIsAuthed
  - useSettings
  - useBalance
  - useVSCodeUrl
  - useUserConversations
  - useUserConversation
  - useGithubUser
  - useCreateConversation
  - useDeleteConversation
  - useUpdateConversation
  - useSubmitFeedback
  - useLogout
  - useUploadFiles
  - useCreateStripeCheckoutSession
- ✅ Migrated components to use RTK Query:
  - ConversationPanel component
  - ConversationCard component

### In Progress

- 🔄 Update components to use the new Redux hooks
- 🔄 Update tests to use RTK Query instead of React Query

### Remaining Tasks

- ⬜ Remove React Query provider from the application
- ⬜ Remove React Query dependencies
- ⬜ Clean up any remaining React Query references
- ⬜ Final testing and validation

## Timeline

- Phase 1 (Setup RTK Query API Service): ✅ Completed
- Phase 2 (Migrate Query Hooks): ✅ Completed
- Phase 3 (Migrate Mutation Hooks): ✅ Completed
- Phase 4 (Update Components): 🔄 In Progress (2-3 days)
- Phase 5 (Clean Up): ⬜ Not Started (1 day)

Estimated completion: 3-4 more days