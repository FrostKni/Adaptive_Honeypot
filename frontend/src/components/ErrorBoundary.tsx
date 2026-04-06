import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({ errorInfo })
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleReportBug = () => {
    const { error, errorInfo } = this.state
    const bugReport = `
**Error Report**
- **Message:** ${error?.message || 'Unknown error'}
- **Stack:** ${error?.stack || 'No stack trace'}
- **Component Stack:** ${errorInfo?.componentStack || 'No component stack'}
- **URL:** ${window.location.href}
- **User Agent:** ${navigator.userAgent}
- **Timestamp:** ${new Date().toISOString()}
    `.trim()

    // Copy to clipboard
    navigator.clipboard.writeText(bugReport).then(() => {
      alert('Error report copied to clipboard!')
    }).catch(() => {
      console.log('Failed to copy to clipboard')
    })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
          <div className="max-w-lg w-full">
            <div className="glass-card p-8 text-center">
              {/* Error Icon */}
              <div className="mx-auto w-20 h-20 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
                <AlertTriangle className="w-10 h-10 text-red-400" />
              </div>

              {/* Error Message */}
              <h1 className="text-2xl font-bold text-white mb-2">
                Something went wrong
              </h1>
              <p className="text-slate-400 mb-6">
                An unexpected error occurred. Please try again or contact support if the problem persists.
              </p>

              {/* Error Details (collapsible) */}
              {this.state.error && (
                <details className="text-left mb-6">
                  <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-300 transition-colors">
                    View error details
                  </summary>
                  <div className="mt-3 p-4 bg-slate-900/50 border border-slate-800/50 rounded-lg overflow-x-auto">
                    <p className="text-red-400 font-mono text-sm mb-2">
                      {this.state.error.message}
                    </p>
                    {this.state.error.stack && (
                      <pre className="text-xs text-slate-400 whitespace-pre-wrap">
                        {this.state.error.stack.split('\n').slice(0, 5).join('\n')}
                      </pre>
                    )}
                  </div>
                </details>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={this.handleRetry}
                  className="btn-primary"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="btn-secondary"
                >
                  <Home className="w-4 h-4" />
                  Go Home
                </button>
                <button
                  onClick={this.handleReportBug}
                  className="btn-secondary"
                >
                  <Bug className="w-4 h-4" />
                  Report Bug
                </button>
              </div>
            </div>

            {/* Help Text */}
            <p className="text-center text-xs text-slate-600 mt-6">
              If this error persists, please check your network connection and try refreshing the page.
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    )
  }
}
