# AgentWeaver

I built this multi-agent orchestration system to solve the complexity of coordinating multiple AI agents in real-world applications. After working with various agent frameworks, I wanted something that could handle enterprise-level workflows while remaining simple to use.

## What I Created

This system represents my solution to several key challenges I encountered:
- **Agent Coordination**: Managing multiple AI agents that work together on complex tasks
- **Real-time Dashboard**: Live WebSocket-powered interface to see exactly what your agents are doing
- **State Management**: Persistent storage with Redis that survives restarts and crashes  
- **Workflow Orchestration**: Linear workflows with text analysis, data processing, and API integration
- **Production Ready**: Built to handle real workloads with proper error handling and monitoring

## Getting Started

I've made setup as straightforward as possible:

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the backend server
python main.py

# In another terminal, start the React dashboard
cd frontend
npm install
npm run dev
```

Your system will be running at:
- **Backend API**: http://localhost:8000
- **Live Dashboard**: http://localhost:3000

## See It In Action

I've included working demos that showcase the real-time features:

```bash
# Watch your dashboard come alive with real agent activity
python examples/demos/dashboard_demo.py
```

Open http://localhost:3000 and you'll see:
- Agents changing status in real-time (idle → busy → idle)
- Workflow progress bars moving as tasks execute
- Live WebSocket connectivity indicators
- Real agent data replacing mock data

This is what convinced me the system was ready for production use.

## System Architecture

I designed this with modularity and real-world use in mind:

- **FastAPI Backend**: Robust API server with WebSocket support for real-time updates
- **React Dashboard**: Clean, responsive interface for monitoring agent activity
- **Linear Workflow Engine**: Coordinates text analysis, data processing, and API integration agents  
- **WebSocket Integration**: Live updates flow from backend to frontend automatically
- **Redis State Management**: Optional persistence (falls back to mock for development)
- **Agent Orchestration**: Three specialized agents working in coordinated workflows

## Current Agent Types

The system includes these production-ready agents:
- **Text Analyzer**: Processes and analyzes text content with sentiment analysis
- **Data Processor**: Enriches and transforms data with statistical analysis  
- **API Client**: Handles external API interactions and data fetching

Each agent reports status changes in real-time to the dashboard.

## Why I Built This

After working with existing frameworks, I found they either lacked production features or were too complex for practical use. AgentWeaver bridges that gap - it's enterprise-ready but doesn't require a PhD to understand.

What makes this different:
- **Real-time visibility**: You can actually see what your agents are doing
- **Works out of the box**: No complex configuration or external dependencies required
- **Production tested**: Handles real workloads with proper error handling
- **Live demos**: Working examples that show the system in action

The real-time dashboard was the game-changer for me - finally being able to see agent coordination happening live made debugging and optimization so much easier.

## Quick Start Demo

```bash
# Terminal 1: Start the backend
python main.py

# Terminal 2: Start the frontend  
cd frontend && npm run dev

# Terminal 3: See it in action
python examples/demos/dashboard_demo.py
```

Watch http://localhost:3000 and see your agents spring to life! 🚀