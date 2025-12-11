/**
 * ErrorBoundary - Global error boundary component
 * 
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 */
import { Component, ErrorInfo, ReactNode } from 'react';
import { colors, spacing, borderRadius } from '../../theme/colors';

interface Props {
    children: ReactNode;
    /** Custom fallback UI */
    fallback?: ReactNode;
    /** Callback when error occurs */
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        this.setState({ errorInfo });

        // Log error to console
        console.error('ErrorBoundary caught an error:', error, errorInfo);

        // Call custom error handler if provided
        this.props.onError?.(error, errorInfo);

        // In production, send to error reporting service
        if (process.env.NODE_ENV === 'production') {
            // Example: sendToErrorReporting(error, errorInfo);
        }
    }

    handleRetry = (): void => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        });
    };

    render(): ReactNode {
        if (this.state.hasError) {
            // Custom fallback
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default fallback UI
            return (
                <div style={{
                    padding: spacing.xl,
                    textAlign: 'center',
                    backgroundColor: colors.background.surface,
                    borderRadius: borderRadius.lg,
                    border: `1px solid ${colors.alert.critical}`,
                    margin: spacing.md
                }}>
                    <div style={{
                        fontSize: '3rem',
                        marginBottom: spacing.md
                    }}>
                        ⚠️
                    </div>
                    <h2 style={{
                        color: colors.text.primary,
                        marginBottom: spacing.sm,
                        fontSize: '1.25rem'
                    }}>
                        Algo deu errado
                    </h2>
                    <p style={{
                        color: colors.text.secondary,
                        marginBottom: spacing.lg,
                        fontSize: '0.875rem'
                    }}>
                        Ocorreu um erro inesperado. Por favor, tente novamente.
                    </p>

                    {/* Error details in development */}
                    {process.env.NODE_ENV === 'development' && this.state.error && (
                        <details style={{
                            marginBottom: spacing.lg,
                            textAlign: 'left',
                            padding: spacing.md,
                            backgroundColor: colors.background.muted,
                            borderRadius: borderRadius.base,
                            fontSize: '0.75rem',
                            fontFamily: 'monospace',
                            overflow: 'auto',
                            maxHeight: '200px'
                        }}>
                            <summary style={{ cursor: 'pointer', marginBottom: spacing.sm }}>
                                Detalhes do Erro
                            </summary>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                {this.state.error.toString()}
                                {this.state.errorInfo && (
                                    <>
                                        {'\n\nComponent Stack:\n'}
                                        {this.state.errorInfo.componentStack}
                                    </>
                                )}
                            </pre>
                        </details>
                    )}

                    <div style={{ display: 'flex', gap: spacing.md, justifyContent: 'center' }}>
                        <button
                            onClick={this.handleRetry}
                            style={{
                                padding: `${spacing.sm} ${spacing.lg}`,
                                backgroundColor: colors.primary.medium,
                                color: '#fff',
                                border: 'none',
                                borderRadius: borderRadius.base,
                                cursor: 'pointer',
                                fontSize: '0.875rem',
                                fontWeight: 500
                            }}
                        >
                            Tentar Novamente
                        </button>
                        <button
                            onClick={() => window.location.href = '/'}
                            style={{
                                padding: `${spacing.sm} ${spacing.lg}`,
                                backgroundColor: 'transparent',
                                color: colors.text.primary,
                                border: `1px solid ${colors.border.default}`,
                                borderRadius: borderRadius.base,
                                cursor: 'pointer',
                                fontSize: '0.875rem'
                            }}
                        >
                            Voltar ao Início
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
