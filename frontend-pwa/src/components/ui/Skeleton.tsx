/**
 * Skeleton Loading Component
 * 
 * Provides visual placeholder while content is loading
 * Sprint 28: UX Improvement
 */

import React from 'react';
import './Skeleton.css';

interface SkeletonProps {
    variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
    width?: string | number;
    height?: string | number;
    animation?: 'pulse' | 'wave' | 'none';
    className?: string;
    count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    variant = 'text',
    width,
    height,
    animation = 'pulse',
    className = '',
    count = 1,
}) => {
    const getVariantClass = () => {
        switch (variant) {
            case 'circular':
                return 'skeleton--circular';
            case 'rectangular':
                return 'skeleton--rectangular';
            case 'rounded':
                return 'skeleton--rounded';
            default:
                return 'skeleton--text';
        }
    };

    const getAnimationClass = () => {
        switch (animation) {
            case 'wave':
                return 'skeleton--wave';
            case 'none':
                return '';
            default:
                return 'skeleton--pulse';
        }
    };

    const style: React.CSSProperties = {
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
    };

    const skeletons = Array.from({ length: count }, (_, index) => (
        <span
            key={index}
            className={`skeleton ${getVariantClass()} ${getAnimationClass()} ${className}`}
            style={style}
            aria-hidden="true"
        />
    ));

    return <>{skeletons}</>;
};

// Pre-built skeleton layouts
export const SkeletonCard: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
    <div className="skeleton-card">
        <Skeleton variant="rectangular" height={180} className="skeleton-card__image" />
        <div className="skeleton-card__content">
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="text" count={lines} />
        </div>
    </div>
);

export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({
    rows = 5,
    columns = 4
}) => (
    <div className="skeleton-table">
        <div className="skeleton-table__header">
            {Array.from({ length: columns }).map((_, i) => (
                <Skeleton key={i} variant="text" height={20} />
            ))}
        </div>
        {Array.from({ length: rows }).map((_, rowIndex) => (
            <div key={rowIndex} className="skeleton-table__row">
                {Array.from({ length: columns }).map((_, colIndex) => (
                    <Skeleton key={colIndex} variant="text" height={16} />
                ))}
            </div>
        ))}
    </div>
);

export const SkeletonList: React.FC<{ items?: number }> = ({ items = 5 }) => (
    <div className="skeleton-list">
        {Array.from({ length: items }).map((_, index) => (
            <div key={index} className="skeleton-list__item">
                <Skeleton variant="circular" width={40} height={40} />
                <div className="skeleton-list__content">
                    <Skeleton variant="text" width="70%" height={16} />
                    <Skeleton variant="text" width="50%" height={14} />
                </div>
            </div>
        ))}
    </div>
);

export const SkeletonProfile: React.FC = () => (
    <div className="skeleton-profile">
        <Skeleton variant="circular" width={80} height={80} />
        <Skeleton variant="text" width={150} height={24} />
        <Skeleton variant="text" width={100} height={16} />
    </div>
);

export default Skeleton;
