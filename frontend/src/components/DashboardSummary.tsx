import React from 'react';

interface DashboardSummaryProps {
  totalAgents: number;
  activeAgents: number;
  totalWorkflows: number;
  activeWorkflows: number;
  lastUpdated: string;
}

const DashboardSummary: React.FC<DashboardSummaryProps> = ({
  totalAgents,
  activeAgents,
  totalWorkflows,
  activeWorkflows,
  lastUpdated
}) => {
  return (
    <div className="dashboard-summary dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">System Overview</h3>
        <div className="last-updated">
          Last updated: {lastUpdated}
        </div>
      </div>
      <div className="dashboard-card-body" style={{ padding: '1rem' }}>
        <div className="summary-grid">
          <div className="summary-item">
            <div className="summary-icon" style={{ backgroundColor: 'rgba(24, 161, 204, 0.1)' }}>
              🤖
            </div>
            <div className="summary-content">
              <div className="summary-value">{totalAgents}</div>
              <div className="summary-label">Total Agents</div>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon" style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)' }}>
              ✅
            </div>
            <div className="summary-content">
              <div className="summary-value">{activeAgents}</div>
              <div className="summary-label">Active Agents</div>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon" style={{ backgroundColor: 'rgba(223, 186, 71, 0.1)' }}>
              📊
            </div>
            <div className="summary-content">
              <div className="summary-value">{totalWorkflows}</div>
              <div className="summary-label">Total Workflows</div>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
              🔄
            </div>
            <div className="summary-content">
              <div className="summary-value">{activeWorkflows}</div>
              <div className="summary-label">Active Workflows</div>
            </div>
          </div>
        </div>
      </div>
      <div className="dashboard-card-footer">
        <button className="action-button">System Status</button>
        <button className="action-button">View Reports</button>
      </div>
    </div>
  );
};

export default DashboardSummary;
