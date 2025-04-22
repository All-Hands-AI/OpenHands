# Git Components Documentation

## Repository Selection Components

### GitRepositoriesSuggestionBox
A component that provides a searchable dropdown for selecting GitHub repositories. It handles both user repositories and public repositories from search results.

### GitRepositorySelector
The core repository selection component that implements:
- Repository search with debounced input
- Loading states with visual feedback
- Empty state handling
- Grouping repositories by provider (GitHub, etc.)

#### Loading States
The repository selector has proper loading state handling:
1. While repositories are loading:
   - Shows a loading spinner in the input field
   - Shows "Loading repositories..." with a spinner in the dropdown
   - Loading state is translated to all supported languages

2. When no results are found (after loading):
   - Shows "No results found" message
   - Message is translated to all supported languages

This loading state implementation ensures users have clear feedback about the current state of repository loading and search results.