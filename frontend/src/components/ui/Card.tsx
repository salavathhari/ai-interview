import React from 'react';
import './Card.css';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  hover,
  onClick,
}) => {
  const classes = [
    'ui-card',
    `ui-card--pad-${padding}`,
    hover && 'ui-card--hover',
    onClick && 'ui-card--clickable',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} onClick={onClick} role={onClick ? 'button' : undefined} tabIndex={onClick ? 0 : undefined}>
      {children}
    </div>
  );
};

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

const CardHeader: React.FC<CardHeaderProps> = ({ title, subtitle, action, icon }) => (
  <div className="ui-card__header">
    <div className="ui-card__header-left">
      {icon && <span className="ui-card__header-icon">{icon}</span>}
      <div>
        <h3 className="ui-card__title">{title}</h3>
        {subtitle && <p className="ui-card__subtitle">{subtitle}</p>}
      </div>
    </div>
    {action && <div className="ui-card__header-action">{action}</div>}
  </div>
);

export { Card, CardHeader };
export default Card;
