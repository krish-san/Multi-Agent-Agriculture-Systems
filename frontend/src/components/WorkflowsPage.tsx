import React, { useState } from 'react';
import './WorkflowsPage.css';
import WorkflowVisualizer from './WorkflowVisualizer';
import type { Workflow, WorkflowStep } from './WorkflowVisualizer';

const WorkflowsPage: React.FC = () => {
  // Sample workflow data
  const sampleWorkflows: Workflow[] = [
    {
      id: 'wf-001',
      name: 'Crop Rotation Planning Workflow',
      status: 'running',
      progress: 0.6,
      startTime: new Date(Date.now() - 35 * 60 * 1000).toISOString(),
      totalDuration: 35 * 60 * 1000,
      steps: [
        {
          id: 'step-1',
          name: 'Initialize Field Data',
          status: 'completed',
          startTime: new Date(Date.now() - 35 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 33 * 60 * 1000).toISOString(),
          duration: 120000,
          output: 'Field data successfully initialized from database.\nLoaded 8 field records with soil composition data.',
          agent: 'data-processing-agent'
        },
        {
          id: 'step-2',
          name: 'Analyze Soil Composition',
          status: 'completed',
          startTime: new Date(Date.now() - 33 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 27 * 60 * 1000).toISOString(),
          duration: 360000,
          output: 'Soil analysis complete. Fields categorized by pH levels and nutrient content.',
          agent: 'soil-analysis-agent'
        },
        {
          id: 'step-3',
          name: 'Generate Crop Options',
          status: 'completed',
          startTime: new Date(Date.now() - 27 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
          duration: 300000,
          output: 'Generated 12 possible crop combinations based on soil analysis and season.',
          agent: 'crop-planning-agent'
        },
        {
          id: 'step-4',
          name: 'Optimize Rotation Schedule',
          status: 'in-progress',
          startTime: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
          agent: 'optimization-agent'
        },
        {
          id: 'step-5',
          name: 'Validate Nutrient Balance',
          status: 'pending',
          agent: 'nutrient-analysis-agent'
        },
        {
          id: 'step-6',
          name: 'Generate Implementation Plan',
          status: 'pending',
          agent: 'planning-agent'
        },
        {
          id: 'step-7',
          name: 'Create Final Report',
          status: 'pending',
          agent: 'reporting-agent'
        }
      ],
      metadata: {
        priority: 'high',
        requestedBy: 'Field Manager',
        fieldCount: 8,
        estimatedCompletion: new Date(Date.now() + 45 * 60 * 1000).toISOString()
      }
    },
    {
      id: 'wf-002',
      name: 'Irrigation Scheduling Workflow',
      status: 'completed',
      progress: 1.0,
      startTime: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      totalDuration: 60 * 60 * 1000,
      steps: [
        {
          id: 'step-1',
          name: 'Load Moisture Sensor Data',
          status: 'completed',
          startTime: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 175 * 60 * 1000).toISOString(),
          duration: 5 * 60 * 1000,
          output: 'Successfully loaded data from 24 moisture sensors across 4 fields.',
          agent: 'sensor-data-agent'
        },
        {
          id: 'step-2',
          name: 'Process Weather Forecast',
          status: 'completed',
          startTime: new Date(Date.now() - 175 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 165 * 60 * 1000).toISOString(),
          duration: 10 * 60 * 1000,
          output: '5-day forecast processed. Expected precipitation: 0.4 inches on Wednesday.',
          agent: 'weather-agent'
        },
        {
          id: 'step-3',
          name: 'Calculate Water Requirements',
          status: 'completed',
          startTime: new Date(Date.now() - 165 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 150 * 60 * 1000).toISOString(),
          duration: 15 * 60 * 1000,
          output: 'Water requirements calculated for all crops based on growth stage and conditions.',
          agent: 'irrigation-calculation-agent'
        },
        {
          id: 'step-4',
          name: 'Optimize Irrigation Schedule',
          status: 'completed',
          startTime: new Date(Date.now() - 150 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 130 * 60 * 1000).toISOString(),
          duration: 20 * 60 * 1000,
          output: 'Schedule optimized to minimize water usage while maintaining crop health.',
          agent: 'optimization-agent'
        },
        {
          id: 'step-5',
          name: 'Generate Irrigation Commands',
          status: 'completed',
          startTime: new Date(Date.now() - 130 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
          duration: 10 * 60 * 1000,
          output: 'Created 16 irrigation commands for the automated system.',
          agent: 'control-system-agent'
        }
      ],
      metadata: {
        priority: 'medium',
        requestedBy: 'Irrigation Manager',
        waterSaved: '18%',
        nextSchedule: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      }
    },
    {
      id: 'wf-003',
      name: 'Pest Detection Analysis',
      status: 'failed',
      progress: 0.33,
      startTime: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() - 3.5 * 60 * 60 * 1000).toISOString(),
      totalDuration: 30 * 60 * 1000,
      steps: [
        {
          id: 'step-1',
          name: 'Process Drone Imagery',
          status: 'completed',
          startTime: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 230 * 60 * 1000).toISOString(),
          duration: 10 * 60 * 1000,
          output: 'Processed 248 high-resolution images from the southern quadrants.',
          agent: 'image-processing-agent'
        },
        {
          id: 'step-2',
          name: 'Detect Anomalies',
          status: 'completed',
          startTime: new Date(Date.now() - 230 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 215 * 60 * 1000).toISOString(),
          duration: 15 * 60 * 1000,
          output: 'Identified 37 potential anomalies in crop patterns.',
          agent: 'anomaly-detection-agent'
        },
        {
          id: 'step-3',
          name: 'Classify Pest Types',
          status: 'failed',
          startTime: new Date(Date.now() - 215 * 60 * 1000).toISOString(),
          endTime: new Date(Date.now() - 210 * 60 * 1000).toISOString(),
          duration: 5 * 60 * 1000,
          error: 'ERROR: ML model failed to load. Classification service unavailable.',
          agent: 'pest-classification-agent'
        },
        {
          id: 'step-4',
          name: 'Generate Intervention Plan',
          status: 'pending',
          agent: 'treatment-planning-agent'
        }
      ],
      metadata: {
        priority: 'high',
        requestedBy: 'Crop Protection Team',
        affectedArea: '12 acres',
        retryScheduled: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
      }
    }
  ];

  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(sampleWorkflows[0]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const handleWorkflowSelect = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
  };

  const handleStepClick = (step: WorkflowStep) => {
    console.log('Step clicked:', step);
  };

  // Filter workflows by status and search query
  const filteredWorkflows = sampleWorkflows
    .filter(wf => filterStatus === 'all' || wf.status === filterStatus)
    .filter(wf => 
      !searchQuery || 
      wf.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      wf.id.toLowerCase().includes(searchQuery.toLowerCase())
    );

  return (
    <div className="workflows-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Workflow Management</h1>
          <p>View and manage agricultural workflows</p>
        </div>
        <div className="header-actions">
          <button className="btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
            </svg>
            Create Workflow
          </button>
        </div>
      </div>

      <div className="filter-section">
        <div className="search-container">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="search-icon">
            <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
          </svg>
          <input 
            type="text" 
            placeholder="Search workflows..." 
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-options">
          <div className="filter-group">
            <label>Status:</label>
            <select 
              className="filter-select" 
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Type:</label>
            <select className="filter-select">
              <option value="all">All Types</option>
              <option value="irrigation">Irrigation</option>
              <option value="planning">Planning</option>
              <option value="monitoring">Monitoring</option>
            </select>
          </div>
        </div>
      </div>

      <div className="workflows-content">
        {/* Workflow List */}
        <div className="workflows-list">
          {filteredWorkflows.map(workflow => (
            <div 
              key={workflow.id}
              className={`workflow-card ${workflow.status} ${selectedWorkflow?.id === workflow.id ? 'selected' : ''}`}
              onClick={() => handleWorkflowSelect(workflow)}
            >
              <div className="workflow-card-header">
                <div className="workflow-name-section">
                  <div className={`status-indicator ${workflow.status}`}></div>
                  <h3>{workflow.name}</h3>
                </div>
                <div className="workflow-actions">
                  <button className="action-btn" onClick={(e) => e.stopPropagation()}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 3a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM10 8.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM11.5 15.5a1.5 1.5 0 10-3 0 1.5 1.5 0 003 0z" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="workflow-card-progress">
                <div className="progress-bar">
                  <div 
                    className={`progress-fill ${workflow.status}`} 
                    style={{ width: `${Math.round(workflow.progress * 100)}%` }}
                  ></div>
                </div>
                <div className="progress-text">
                  {Math.round(workflow.progress * 100)}% Complete
                </div>
              </div>

              <div className="workflow-card-details">
                <div className="detail-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="detail-icon">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clipRule="evenodd" />
                  </svg>
                  <span>Started: {new Date(workflow.startTime).toLocaleTimeString()}</span>
                </div>
                <div className="detail-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="detail-icon">
                    <path fillRule="evenodd" d="M5.75 2a.75.75 0 01.75.75V4h7V2.75a.75.75 0 011.5 0V4h.25A2.75 2.75 0 0118 6.75v8.5A2.75 2.75 0 0115.25 18H4.75A2.75 2.75 0 012 15.25v-8.5A2.75 2.75 0 014.75 4H5V2.75A.75.75 0 015.75 2zm-1 5.5c-.69 0-1.25.56-1.25 1.25v6.5c0 .69.56 1.25 1.25 1.25h10.5c.69 0 1.25-.56 1.25-1.25v-6.5c0-.69-.56-1.25-1.25-1.25H4.75z" clipRule="evenodd" />
                  </svg>
                  <span>Steps: {workflow.steps.filter(s => s.status === 'completed').length}/{workflow.steps.length}</span>
                </div>
              </div>

              <div className="workflow-card-footer">
                <div className="priority-badge">
                  Priority: {workflow.metadata?.priority || 'normal'}
                </div>
                <div className="workflow-id">{workflow.id}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Details Panel */}
        {selectedWorkflow && (
          <div className="workflow-detail-panel">
            <div className="panel-header">
              <div className="panel-title">
                <div className={`status-indicator ${selectedWorkflow.status}`}></div>
                <h2>{selectedWorkflow.name}</h2>
              </div>
              <div className="status-badge">
                {selectedWorkflow.status}
              </div>
            </div>

            {/* Workflow Visualizer Component */}
            <div className="workflow-visualization">
              <WorkflowVisualizer 
                workflow={selectedWorkflow} 
                onStepClick={handleStepClick}
              />
            </div>

            {/* Execution Steps */}
            <div className="execution-steps">
              <h3>Execution Steps</h3>
              <div className="steps-list">
                {selectedWorkflow.steps.map((step, index) => (
                  <div 
                    key={step.id}
                    className={`step-item ${step.status}`}
                    onClick={() => handleStepClick(step)}
                  >
                    <div className="step-content">
                      <div className="step-header">
                        <strong className="step-name">{step.name}</strong>
                        <div className={`step-status ${step.status}`}>
                          {step.status.replace('-', ' ')}
                        </div>
                      </div>
                      
                      {step.agent && (
                        <div className="step-agent">
                          <span>🤖</span>
                          <small>Agent: {step.agent}</small>
                        </div>
                      )}
                      
                      {step.status !== 'pending' && (
                        <div className="step-time">
                          {step.startTime && <span>Started: {new Date(step.startTime).toLocaleTimeString()}</span>}
                          {step.duration && <span>Duration: {(step.duration / 60000).toFixed(1)} min</span>}
                        </div>
                      )}
                      
                      {step.status === 'completed' && step.output && (
                        <div className="step-output">
                          <div className="output-preview">
                            <span style={{ opacity: '0.7' }}>Output: </span>
                            {step.output?.split('\n')[0]}
                          </div>
                        </div>
                      )}
                      
                      {step.error && (
                        <div className="step-error">
                          <div className="error-message">{step.error}</div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="workflow-actions-panel">
              <div className="action-buttons">
                {selectedWorkflow.status === 'running' && (
                  <button className="action-button danger">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                    </svg>
                    Pause Workflow
                  </button>
                )}
                {selectedWorkflow.status === 'pending' && (
                  <button className="action-button primary">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                    </svg>
                    Start Workflow
                  </button>
                )}
                {selectedWorkflow.status === 'failed' && (
                  <button className="action-button primary">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z" clipRule="evenodd" />
                    </svg>
                    Retry Workflow
                  </button>
                )}
                <button className="action-button">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                  </svg>
                  View Details
                </button>
                <button className="action-button">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  Export Data
                </button>
                <button className="action-button">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                  </svg>
                  Clone Workflow
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowsPage;
