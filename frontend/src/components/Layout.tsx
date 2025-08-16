import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import ChatBot from './ChatBot';
import './Layout.css';

interface NavItem {
  icon: string;
  name: string;
  path: string;
}

const Layout = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  const navItems: NavItem[] = [
    { icon: '📊', name: 'Dashboard', path: '/' },
    { icon: '✈️', name: 'Workflows', path: '/workflows' },
    { icon: '🤖', name: 'Agents', path: '/agents' },
    { icon: '📝', name: 'Reports', path: '/reports' },
    { icon: '📈', name: 'Statistics', path: '/statistics' },
  ];

  return (
    <div className="dashboard">
      {/* ChatBot positioned at the end for proper layering */}
      <nav className="sidebar">
        <div className="user-profile">
          <div className="avatar">
            <span>AG</span>
          </div>
          <div className="user-info">
            <h3>AgentWeaver</h3>
            <p>Agricultural System</p>
          </div>
        </div>
        
        <div className="nav-items">
          {navItems.map((item) => (
            <NavLink 
              key={item.path}
              to={item.path}
              className={({ isActive }) => 
                `nav-item ${isActive ? 'active' : ''}`
              }
              end={item.path === '/'}
              onClick={() => {
                // Direct navigation using window.location to ensure it works
                // This is a fallback solution if React Router isn't handling links properly
                console.log(`Navigating to: ${item.path}`);
                window.location.href = item.path;
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-name">{item.name}</span>
            </NavLink>
          ))}
        </div>
        
        <div className="system-stats">
          <div className="stat-item">
            <span className="stat-icon">🔄</span>
            <span className="stat-label">Active Workflows:</span>
            <span className="stat-value">3</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">📊</span>
            <span className="stat-label">Total Workflows:</span>
            <span className="stat-value">7</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🔌</span>
            <span className="stat-label">Connected Clients:</span>
            <span className="stat-value">1</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🤖</span>
            <span className="stat-label">Active Agents:</span>
            <span className="stat-value">5</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">⚡</span>
            <span className="stat-label">System Status:</span>
            <span className="stat-value connected">Ready</span>
          </div>
        </div>
        
        <div className="connected-users">
          <h4>Online Users</h4>
          <div className="user-avatars">
            <div className="user-avatar">AK</div>
            <div className="user-avatar">JD</div>
            <div className="user-avatar">RB</div>
            <div className="user-avatar">+2</div>
          </div>
        </div>
      </nav>

      <div className="main-content">
        <Outlet />
      </div>
      
      {/* ChatBot added at the end to ensure proper stacking order */}
      <ChatBot />
    </div>
  );
};

export default Layout;
