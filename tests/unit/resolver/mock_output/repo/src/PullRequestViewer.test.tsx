

import React from 'react';
import { render, screen } from '@testing-library/react';
import PullRequestViewer from './PullRequestViewer';

describe('PullRequestViewer', () => {
  it('renders the component title', () => {
    render(<PullRequestViewer />);
    const titleElement = screen.getByText(/Pull Request Viewer/i);
    expect(titleElement).toBeInTheDocument();
  });

  it('renders the repository select dropdown', () => {
    render(<PullRequestViewer />);
    const selectElement = screen.getByRole('combobox', { name: /select a repository/i });
    expect(selectElement).toBeInTheDocument();
  });
});
