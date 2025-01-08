import React from 'react';
import { ErrorToast } from '~/components/shared/error-toast';
import { AgentList } from './agent-list';

interface Props {
  children: React.ReactNode;
}

interface State {
  error: Error | null;
}

class DynamicAgentErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to error reporting service
    // eslint-disable-next-line no-console
    console.error('Dynamic Agent Error:', error, errorInfo);
  }

  render(): React.ReactNode {
    const { error } = this.state;
    const { children } = this.props;

    if (error) {
      return (
        <div className="p-4">
          <h3 className="text-lg font-medium text-red-600 mb-2">
            Something went wrong
          </h3>
          <ErrorToast 
            id="dynamic-agent-error"
            error={error.toString()}
          />
        </div>
      );
    }

    return children;
  }
}

export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> {
  function WithErrorBoundary(props: P) {
    // eslint-disable-next-line react/jsx-props-no-spreading
    const componentProps = { ...props };
    return (
      <DynamicAgentErrorBoundary>
        <WrappedComponent {...componentProps} />
      </DynamicAgentErrorBoundary>
    );
  }
  WithErrorBoundary.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithErrorBoundary;
}

export const AgentListWithErrorBoundary = withErrorBoundary(AgentList);