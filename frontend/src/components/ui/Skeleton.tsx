import React from 'react';
import './Skeleton.css';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circle' | 'rect';
  className?: string;
  lines?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  variant = 'text',
  className = '',
  lines,
}) => {
  if (lines && lines > 1) {
    return (
      <div className={`skeleton-block ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`skeleton skeleton--${variant}`}
            style={{
              width: i === lines - 1 ? '60%' : '100%',
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`skeleton skeleton--${variant} ${className}`}
      style={{ width, height }}
    />
  );
};

interface StatSkeletonProps {
  count?: number;
}

const StatSkeleton: React.FC<StatSkeletonProps> = ({ count = 4 }) => (
  <div className="stat-skeleton-grid" style={{ display: 'grid', gridTemplateColumns: `repeat(${count}, 1fr)`, gap: '1rem' }}>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="skeleton-stat-card">
        <Skeleton width="40%" height="0.75rem" />
        <Skeleton width="60%" height="1.5rem" variant="rect" />
        <Skeleton width="80%" height="0.625rem" />
      </div>
    ))}
  </div>
);

export { Skeleton, StatSkeleton };
export default Skeleton;
