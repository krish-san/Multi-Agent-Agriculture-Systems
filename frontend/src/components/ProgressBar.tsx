import React from 'react';

interface ProgressBarProps {
  progress: number; // 0 to 1
  height?: number;
  color?: string;
  backgroundColor?: string;
  animate?: boolean;
  label?: boolean;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  height = 6,
  color = '#22C55E',
  backgroundColor = 'rgba(34, 197, 94, 0.1)',
  animate = true,
  label = false,
  className
}) => {
  const percentage = Math.min(Math.max(Math.round(progress * 100), 0), 100);
  
  return (
    <div className={`progress-bar-container ${className || ''}`}>
      {label && (
        <div className="progress-label">
          <span>{percentage}%</span>
        </div>
      )}
      <div 
        className="progress-track" 
        style={{ 
          height: `${height}px`, 
          backgroundColor,
          borderRadius: height / 2
        }}
      >
        <div 
          className={`progress-fill ${animate ? 'animate' : ''}`}
          style={{ 
            width: `${percentage}%`, 
            backgroundColor: color,
            borderRadius: height / 2,
            transition: animate ? 'width 0.5s ease-out' : 'none'
          }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
