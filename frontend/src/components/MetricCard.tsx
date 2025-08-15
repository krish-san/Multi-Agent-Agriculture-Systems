import React from 'react';

interface MetricCardProps {
  title: string;
  value: number | string;
  total?: number | string;
  subtitle?: string;
  icon: string;
  color: string;
  onClick?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  total,
  subtitle,
  icon,
  color,
  onClick
}) => {
  return (
    <div 
      className="metric-card" 
      onClick={onClick}
      style={{
        cursor: onClick ? 'pointer' : 'default'
      }}
    >
      <span className="metric-title">{title}</span>
      <div className="metric-value-container">
        <span 
          className="metric-value"
          style={{ color }}
        >
          {value}
        </span>
        {total && <span className="metric-total">/{total}</span>}
      </div>
      {subtitle && <span className="metric-subtitle">{subtitle}</span>}
      <div 
        className="metric-icon"
        style={{ backgroundColor: `${color}15` }}
      >
        {icon}
      </div>
    </div>
  );
};

export default MetricCard;
