import { render, screen, waitFor } from '@testing-library/react';
import { CostStatsModal } from '#/components/modals/cost-stats-modal';
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('CostStatsModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    render(<CostStatsModal isOpen={false} onClose={() => {}} />);
    expect(screen.queryByText('Cost Statistics')).not.toBeInTheDocument();
  });

  it('should render loading state initially', () => {
    render(<CostStatsModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render cost data when loaded', async () => {
    const mockCostData = {
      accumulated_cost: 0.5,
      costs: [
        { model: 'gpt-4', cost: 0.2, timestamp: Date.now() / 1000 },
        { model: 'gpt-3.5', cost: 0.3, timestamp: Date.now() / 1000 },
      ],
    };

    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve(mockCostData),
    });

    render(<CostStatsModal isOpen={true} onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText('Total Cost: $0.5000')).toBeInTheDocument();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
      expect(screen.getByText('gpt-3.5')).toBeInTheDocument();
    });
  });

  it('should handle errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    render(<CostStatsModal isOpen={true} onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Error loading cost data/)).toBeInTheDocument();
    });
  });
});
