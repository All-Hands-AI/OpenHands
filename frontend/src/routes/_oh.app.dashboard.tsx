
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Container } from '~/components/layout/container';
import { LoadingSpinner } from '~/components/shared/loading-spinner';
import { ErrorToast } from '~/components/shared/error-toast';
import { DashboardIcon } from '~/icons/dashboard';

export default function Dashboard() {
  interface DashboardStats {
    activeAgents: number;
    indexedAgents: number;
    systemLoad: number;
    activeWorkflows: number;
  }

  const { data: stats, isLoading, error } = useQuery<DashboardStats>({ 
    queryKey: ['dashboard-stats'], 
    queryFn: async () => {
      // Replace with actual API call when backend is ready
      return {
        activeAgents: 3,
        indexedAgents: 5,
        systemLoad: 0.45,
        activeWorkflows: 2
      };
    }
  });

  if (isLoading || !stats) return <LoadingSpinner size="small" />;
  if (error) return <ErrorToast id="dashboard-error" error={error instanceof Error ? error.message : String(error)} />;

  return (
    <Container>
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Active Agents */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-gray-500 text-sm font-medium">Active Agents</h3>
              <DashboardIcon className="h-6 w-6 text-gray-400" />
            </div>
            <p className="mt-2 text-3xl font-semibold">{stats.activeAgents}</p>
          </div>

          {/* Indexed Agents */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-gray-500 text-sm font-medium">Indexed Agents</h3>
              <DashboardIcon className="h-6 w-6 text-gray-400" />
            </div>
            <p className="mt-2 text-3xl font-semibold">{stats.indexedAgents}</p>
          </div>

          {/* System Load */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-gray-500 text-sm font-medium">System Load</h3>
              <DashboardIcon className="h-6 w-6 text-gray-400" />
            </div>
            <p className="mt-2 text-3xl font-semibold">{(stats.systemLoad * 100).toFixed(1)}%</p>
          </div>

          {/* Active Workflows */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-gray-500 text-sm font-medium">Active Workflows</h3>
              <DashboardIcon className="h-6 w-6 text-gray-400" />
            </div>
            <p className="mt-2 text-3xl font-semibold">{stats.activeWorkflows}</p>
          </div>
        </div>
      </div>
    </Container>
  );
}
