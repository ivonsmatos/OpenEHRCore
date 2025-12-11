import React from 'react';
import './PaginatedResults.css';

export interface PaginatedResultsProps {
    /** Total number of items */
    total: number;
    /** Current page number (1-indexed) */
    currentPage: number;
    /** Number of items per page */
    pageSize: number;
    /** Available page size options */
    pageSizeOptions?: number[];
    /** Called when page changes */
    onPageChange: (page: number) => void;
    /** Called when page size changes */
    onPageSizeChange: (size: number) => void;
    /** Whether data is loading */
    loading?: boolean;
    /** Additional CSS class */
    className?: string;
}

/**
 * PaginatedResults Component
 * 
 * Pagination controls with:
 * - Page numbers
 * - Previous/Next buttons
 * - Items per page selector
 * - Total count display
 */
export const PaginatedResults: React.FC<PaginatedResultsProps> = ({
    total,
    currentPage,
    pageSize,
    pageSizeOptions = [10, 20, 50, 100],
    onPageChange,
    onPageSizeChange,
    loading = false,
    className = ''
}) => {
    const totalPages = Math.ceil(total / pageSize);
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, total);

    const handlePrevious = () => {
        if (currentPage > 1) {
            onPageChange(currentPage - 1);
        }
    };

    const handleNext = () => {
        if (currentPage < totalPages) {
            onPageChange(currentPage + 1);
        }
    };

    const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(e.target.value, 10);
        onPageSizeChange(newSize);
        // Reset to first page when changing page size
        onPageChange(1);
    };

    // Generate page numbers to display
    const getPageNumbers = (): (number | string)[] => {
        const pages: (number | string)[] = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);

            // Calculate range around current page
            let start = Math.max(2, currentPage - 1);
            let end = Math.min(totalPages - 1, currentPage + 1);

            // Add ellipsis if needed
            if (start > 2) {
                pages.push('...');
            }

            // Add middle pages
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            // Add ellipsis if needed
            if (end < totalPages - 1) {
                pages.push('...');
            }

            // Always show last page
            pages.push(totalPages);
        }

        return pages;
    };

    if (total === 0) {
        return (
            <div className={`paginated-results ${className}`}>
                <div className="paginated-results__info">
                    Nenhum resultado encontrado
                </div>
            </div>
        );
    }

    return (
        <div className={`paginated-results ${className} ${loading ? 'paginated-results--loading' : ''}`}>
            <div className="paginated-results__info">
                <span className="paginated-results__count">
                    Mostrando {startItem}-{endItem} de {total} resultados
                </span>

                <div className="paginated-results__page-size">
                    <label htmlFor="page-size">Itens por página:</label>
                    <select
                        id="page-size"
                        value={pageSize}
                        onChange={handlePageSizeChange}
                        disabled={loading}
                    >
                        {pageSizeOptions.map(size => (
                            <option key={size} value={size}>{size}</option>
                        ))}
                    </select>
                </div>
            </div>

            <nav className="paginated-results__nav" aria-label="Paginação">
                <button
                    type="button"
                    className="paginated-results__btn paginated-results__btn--prev"
                    onClick={handlePrevious}
                    disabled={currentPage === 1 || loading}
                    aria-label="Página anterior"
                >
                    ← Anterior
                </button>

                <div className="paginated-results__pages">
                    {getPageNumbers().map((page, index) => (
                        typeof page === 'number' ? (
                            <button
                                key={index}
                                type="button"
                                className={`paginated-results__page ${currentPage === page ? 'paginated-results__page--active' : ''}`}
                                onClick={() => onPageChange(page)}
                                disabled={loading}
                                aria-current={currentPage === page ? 'page' : undefined}
                            >
                                {page}
                            </button>
                        ) : (
                            <span key={index} className="paginated-results__ellipsis">
                                {page}
                            </span>
                        )
                    ))}
                </div>

                <button
                    type="button"
                    className="paginated-results__btn paginated-results__btn--next"
                    onClick={handleNext}
                    disabled={currentPage === totalPages || loading}
                    aria-label="Próxima página"
                >
                    Próxima →
                </button>
            </nav>
        </div>
    );
};

export default PaginatedResults;
