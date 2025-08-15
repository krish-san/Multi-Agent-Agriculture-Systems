import React, { useState } from 'react';
import './StatisticsPage.css';

// Define types for statistics data
interface StatisticCard {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: string;
  color: string;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color: string;
  }[];
}

interface ComparisonData {
  title: string;
  current: number;
  previous: number;
  unit: string;
  change: number;
}

const StatisticsPage: React.FC = () => {
  // Sample statistics data
  const mainStats: StatisticCard[] = [
    {
      title: 'Total Yield',
      value: '1,254',
      change: 8.2,
      changeType: 'positive',
      icon: '🌾',
      color: '#22C55E'
    },
    {
      title: 'Water Usage',
      value: '34,280',
      change: -12.5,
      changeType: 'positive',
      icon: '💧',
      color: '#3B82F6'
    },
    {
      title: 'Field Efficiency',
      value: '87%',
      change: 2.8,
      changeType: 'positive',
      icon: '📊',
      color: '#DFBA47'
    },
    {
      title: 'Operating Costs',
      value: '$42,150',
      change: 5.3,
      changeType: 'negative',
      icon: '💰',
      color: '#EF4444'
    }
  ];

  // Sample chart data
  const monthlyYieldData: ChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    datasets: [
      {
        label: 'Corn',
        data: [65, 72, 78, 75, 85, 92, 96],
        color: '#DFBA47'
      },
      {
        label: 'Wheat',
        data: [42, 45, 48, 52, 55, 59, 63],
        color: '#22C55E'
      },
      {
        label: 'Soybeans',
        data: [28, 35, 36, 32, 39, 45, 52],
        color: '#3B82F6'
      }
    ]
  };

  const resourceUtilization: { category: string; value: number; color: string }[] = [
    { category: 'Water', value: 75, color: '#3B82F6' },
    { category: 'Fertilizer', value: 65, color: '#22C55E' },
    { category: 'Electricity', value: 50, color: '#F59E0B' },
    { category: 'Fuel', value: 40, color: '#EF4444' },
    { category: 'Labor', value: 80, color: '#8B5CF6' }
  ];

  const fieldComparisons: ComparisonData[] = [
    {
      title: 'North Field',
      current: 92,
      previous: 85,
      unit: 'bu/acre',
      change: 8.2
    },
    {
      title: 'South Field',
      current: 78,
      previous: 75,
      unit: 'bu/acre',
      change: 4.0
    },
    {
      title: 'East Field',
      current: 85,
      previous: 90,
      unit: 'bu/acre',
      change: -5.6
    },
    {
      title: 'West Field',
      current: 105,
      previous: 95,
      unit: 'bu/acre',
      change: 10.5
    }
  ];

  // Sample time periods
  const timePeriods = ['Last 7 Days', 'Last 30 Days', 'This Month', 'Last Quarter', 'Year to Date', 'Custom'];
  
  const [selectedTimePeriod, setSelectedTimePeriod] = useState('Last 30 Days');
  const [selectedMetric, setSelectedMetric] = useState('All Metrics');

  // Sample metrics filter options
  const metricOptions = [
    'All Metrics',
    'Yield Performance',
    'Resource Usage',
    'Cost Analysis',
    'Efficiency Metrics',
    'Environmental Impact'
  ];

  // Helper function for displaying change with sign and color
  const renderChange = (change: number, changeType?: 'positive' | 'negative' | 'neutral') => {
    let displayType = changeType;
    
    // If changeType is not provided, determine based on change value
    if (!displayType) {
      displayType = change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral';
    }
    
    const classes = `stat-change ${displayType}`;
    const prefix = change > 0 ? '+' : '';
    
    return (
      <span className={classes}>
        {prefix}{change}%
      </span>
    );
  };

  // Function to render a fake chart (would be replaced with real chart component)
  const renderFakeChart = (type: 'bar' | 'line' | 'pie' | 'utilization') => {
    if (type === 'utilization') {
      return (
        <div className="utilization-chart">
          {resourceUtilization.map((item, index) => (
            <div className="utilization-item" key={index}>
              <div className="utilization-label">
                <span>{item.category}</span>
                <span>{item.value}%</span>
              </div>
              <div className="utilization-bar-container">
                <div 
                  className="utilization-bar" 
                  style={{ 
                    width: `${item.value}%`, 
                    backgroundColor: item.color 
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      );
    }
  
    return (
      <div className={`fake-chart ${type}-chart`}>
        {type === 'bar' && (
          <div className="chart-bars">
            {monthlyYieldData.labels.map((label, index) => (
              <div className="chart-month" key={index}>
                {monthlyYieldData.datasets.map((dataset, datasetIndex) => (
                  <div 
                    key={datasetIndex}
                    className="chart-bar"
                    style={{ 
                      height: `${dataset.data[index] / 2}px`,
                      backgroundColor: dataset.color,
                      marginLeft: datasetIndex > 0 ? '3px' : '0'
                    }}
                  ></div>
                ))}
                <div className="chart-label">{label}</div>
              </div>
            ))}
          </div>
        )}
        
        {type === 'line' && (
          <div className="chart-placeholder">
            <div className="chart-line"></div>
            <div className="chart-line secondary"></div>
            <div className="chart-grid">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="chart-grid-line"></div>
              ))}
            </div>
          </div>
        )}
        
        {type === 'pie' && (
          <div className="chart-pie">
            <div className="pie-segment segment1"></div>
            <div className="pie-segment segment2"></div>
            <div className="pie-segment segment3"></div>
            <div className="pie-center"></div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="statistics-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Statistics & Analytics</h1>
          <p>Key performance metrics and agricultural analytics</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            Export Data
          </button>
          <button className="btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            View Detailed Reports
          </button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="time-filter">
          <label>Time Period:</label>
          <div className="time-buttons">
            {timePeriods.map((period) => (
              <button
                key={period}
                className={`time-button ${selectedTimePeriod === period ? 'active' : ''}`}
                onClick={() => setSelectedTimePeriod(period)}
              >
                {period}
              </button>
            ))}
          </div>
        </div>
        <div className="metrics-filter">
          <label>Filter Metrics:</label>
          <select
            className="metric-select"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
          >
            {metricOptions.map((metric) => (
              <option key={metric} value={metric}>{metric}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Statistics Cards */}
      <div className="stats-cards">
        {mainStats.map((stat, index) => (
          <div className="stat-card" key={index}>
            <div className="stat-icon" style={{ backgroundColor: `${stat.color}20` }}>
              <span style={{ color: stat.color }}>{stat.icon}</span>
            </div>
            <div className="stat-content">
              <h3 className="stat-title">{stat.title}</h3>
              <div className="stat-value-container">
                <span className="stat-value">{stat.value}</span>
                {stat.change !== undefined && renderChange(stat.change, stat.changeType)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts and Detailed Statistics */}
      <div className="analytics-section">
        <div className="analytics-grid">
          {/* Monthly Yield Chart */}
          <div className="analytics-card wide">
            <div className="card-header">
              <h3>Monthly Yield Performance</h3>
              <div className="card-actions">
                <button className="card-action-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="card-content">
              {renderFakeChart('bar')}
              <div className="chart-legend">
                {monthlyYieldData.datasets.map((dataset, index) => (
                  <div className="legend-item" key={index}>
                    <div className="legend-color" style={{ backgroundColor: dataset.color }}></div>
                    <span>{dataset.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Resource Utilization */}
          <div className="analytics-card">
            <div className="card-header">
              <h3>Resource Utilization</h3>
              <div className="card-actions">
                <button className="card-action-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="card-content">
              {renderFakeChart('utilization')}
            </div>
          </div>
          
          {/* Cost Breakdown */}
          <div className="analytics-card">
            <div className="card-header">
              <h3>Cost Breakdown</h3>
              <div className="card-actions">
                <button className="card-action-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="card-content">
              {renderFakeChart('pie')}
              <div className="chart-legend pie-legend">
                <div className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: '#DFBA47' }}></div>
                  <span>Labor (45%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: '#3B82F6' }}></div>
                  <span>Materials (30%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: '#EF4444' }}></div>
                  <span>Equipment (25%)</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Field Comparison */}
          <div className="analytics-card wide">
            <div className="card-header">
              <h3>Field Performance Comparison</h3>
              <div className="card-actions">
                <button className="card-action-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="card-content">
              <div className="comparison-table">
                <table>
                  <thead>
                    <tr>
                      <th>Field Name</th>
                      <th>Current Yield</th>
                      <th>Previous Yield</th>
                      <th>Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fieldComparisons.map((field, index) => (
                      <tr key={index}>
                        <td>{field.title}</td>
                        <td><strong>{field.current} {field.unit}</strong></td>
                        <td>{field.previous} {field.unit}</td>
                        <td className={field.change > 0 ? 'positive' : 'negative'}>
                          {field.change > 0 ? '+' : ''}{field.change}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          {/* Seasonal Trends */}
          <div className="analytics-card wide">
            <div className="card-header">
              <h3>Seasonal Trends</h3>
              <div className="card-actions">
                <button className="card-action-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="card-content">
              {renderFakeChart('line')}
              <div className="chart-legend">
                <div className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: '#22C55E' }}></div>
                  <span>This Year</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: '#94A3B8' }}></div>
                  <span>Previous Year</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPage;
