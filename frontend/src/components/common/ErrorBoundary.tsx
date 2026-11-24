import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component tree:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[300px] flex items-center justify-center p-6 bg-slate-900/60 rounded-xl border border-red-500/30 text-center">
          <div className="max-w-md space-y-4">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto animate-pulse" />
            <h2 className="text-xl font-bold text-white tracking-wide">Telemetry Subsystem Error</h2>
            <p className="text-slate-400 text-sm">
              An unexpected fault occurred in the rendering pipeline. The error has been captured.
            </p>
            <p className="text-xs font-mono text-red-300/80 bg-red-950/40 p-2 rounded border border-red-800/40 truncate">
              {this.state.error?.message || 'Unknown runtime error'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold rounded-lg text-sm transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Reset Component
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
