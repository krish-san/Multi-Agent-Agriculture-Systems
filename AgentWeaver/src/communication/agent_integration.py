
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..orchestration.supervisor import SupervisorNode
from ..agents import (
    BaseWorkerAgent,
    TextAnalysisAgent,
    APIInteractionAgent,
    DataProcessingAgent
)
from ..core.models import AgentCapability, AgentStatus, SystemState

logger = logging.getLogger(__name__)


class AgentRegistry:
    
    def __init__(self, supervisor: Optional[SupervisorNode] = None):
        self.supervisor = supervisor or SupervisorNode()
        self.registered_agents: Dict[str, BaseWorkerAgent] = {}
        self.logger = logging.getLogger(f"{__name__}.AgentRegistry")
        
    def create_default_agents(self) -> List[BaseWorkerAgent]:
        agents = []
        
        try:
            # Create Text Analysis Agent
            text_agent = TextAnalysisAgent(name="MainTextAnalyzer")
            agents.append(text_agent)
            self.logger.info(f"Created Text Analysis Agent: {text_agent.agent_id}")
            
            # Create API Interaction Agent
            api_agent = APIInteractionAgent(name="MainAPIClient")
            agents.append(api_agent)
            self.logger.info(f"Created API Interaction Agent: {api_agent.agent_id}")
            
            # Create Data Processing Agent
            data_agent = DataProcessingAgent(name="MainDataProcessor")
            agents.append(data_agent)
            self.logger.info(f"Created Data Processing Agent: {data_agent.agent_id}")
            
            self.logger.info(f"Successfully created {len(agents)} default agents")
            
        except Exception as e:
            self.logger.error(f"Failed to create default agents: {str(e)}")
            raise
        
        return agents
    
    def register_agent_with_supervisor(self, agent: BaseWorkerAgent) -> bool:
        try:
            # Prepare agent data for supervisor registration
            agent_data = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "agent_type": agent.agent_state.agent_type,
                "capabilities": [cap.value for cap in agent.capabilities],
                "status": agent.status.value,
                "max_concurrent_tasks": agent.agent_state.max_concurrent_tasks,
                "timeout_seconds": agent.agent_state.timeout_seconds
            }
            
            # Register with supervisor
            result = self.supervisor.register_agent(agent_data)
            
            if result.get("success", False):
                # Store reference to the agent
                self.registered_agents[agent.agent_id] = agent
                self.logger.info(f"Successfully registered agent {agent.name} ({agent.agent_id})")
                return True
            else:
                error_msg = result.get("error", "Unknown registration error")
                self.logger.error(f"Failed to register agent {agent.name}: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during agent registration for {agent.name}: {str(e)}")
            return False
    
    def register_all_agents(self, agents: Optional[List[BaseWorkerAgent]] = None) -> Dict[str, Any]:
        if agents is None:
            agents = self.create_default_agents()
        
        results = {
            "total_agents": len(agents),
            "successful_registrations": 0,
            "failed_registrations": 0,
            "registered_agent_ids": [],
            "failed_agent_ids": [],
            "errors": []
        }
        
        self.logger.info(f"Starting registration of {len(agents)} agents")
        
        for agent in agents:
            try:
                success = self.register_agent_with_supervisor(agent)
                
                if success:
                    results["successful_registrations"] += 1
                    results["registered_agent_ids"].append(agent.agent_id)
                else:
                    results["failed_registrations"] += 1
                    results["failed_agent_ids"].append(agent.agent_id)
                    
            except Exception as e:
                results["failed_registrations"] += 1
                results["failed_agent_ids"].append(agent.agent_id)
                results["errors"].append(f"Agent {agent.name}: {str(e)}")
                self.logger.error(f"Failed to register agent {agent.name}: {str(e)}")
        
        self.logger.info(
            f"Agent registration complete: {results['successful_registrations']} successful, "
            f"{results['failed_registrations']} failed"
        )
        
        return results
    
    def unregister_agent(self, agent_id: str) -> bool:
        try:
            result = self.supervisor.unregister_agent(agent_id)
            
            if result.get("success", False):
                # Remove from local registry
                if agent_id in self.registered_agents:
                    agent_name = self.registered_agents[agent_id].name
                    del self.registered_agents[agent_id]
                    self.logger.info(f"Successfully unregistered agent {agent_name} ({agent_id})")
                else:
                    self.logger.warning(f"Agent {agent_id} was not in local registry")
                return True
            else:
                error_msg = result.get("error", "Unknown unregistration error")
                self.logger.error(f"Failed to unregister agent {agent_id}: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during agent unregistration for {agent_id}: {str(e)}")
            return False
    
    def get_registered_agents(self) -> Dict[str, BaseWorkerAgent]:
        return self.registered_agents.copy()
    
    def get_agent_by_capability(self, capability: AgentCapability) -> List[BaseWorkerAgent]:
        matching_agents = []
        
        for agent in self.registered_agents.values():
            if capability in agent.capabilities:
                matching_agents.append(agent)
        
        return matching_agents
    
    def perform_health_checks(self) -> Dict[str, Any]:
        results = {
            "total_agents": len(self.registered_agents),
            "healthy_agents": 0,
            "unhealthy_agents": 0,
            "health_status": {}
        }
        
        for agent_id, agent in self.registered_agents.items():
            try:
                is_healthy = agent.health_check()
                results["health_status"][agent_id] = {
                    "name": agent.name,
                    "healthy": is_healthy,
                    "status": agent.status.value,
                    "error_message": agent.agent_state.error_message,
                    "last_activity": agent.agent_state.last_activity.isoformat()
                }
                
                if is_healthy:
                    results["healthy_agents"] += 1
                else:
                    results["unhealthy_agents"] += 1
                    
            except Exception as e:
                results["unhealthy_agents"] += 1
                results["health_status"][agent_id] = {
                    "name": agent.name,
                    "healthy": False,
                    "status": "error",
                    "error_message": f"Health check failed: {str(e)}",
                    "last_activity": None
                }
                self.logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
        
        return results
    
    def shutdown_all_agents(self) -> None:
        self.logger.info("Shutting down all registered agents...")
        
        for agent_id, agent in list(self.registered_agents.items()):
            try:
                # Unregister from supervisor
                self.unregister_agent(agent_id)
                
                # Perform any agent-specific cleanup
                if hasattr(agent, 'shutdown'):
                    agent.shutdown()
                    
            except Exception as e:
                self.logger.error(f"Error during shutdown of agent {agent_id}: {str(e)}")
        
        self.registered_agents.clear()
        self.logger.info("All agents shutdown complete")


def initialize_agent_system(supervisor: Optional[SupervisorNode] = None) -> AgentRegistry:
    logger.info("Initializing AgentWeaver agent system...")
    
    # Create agent registry
    registry = AgentRegistry(supervisor)
    
    # Register all default agents
    registration_results = registry.register_all_agents()
    
    # Log results
    if registration_results["successful_registrations"] > 0:
        logger.info(
            f"Agent system initialized successfully with "
            f"{registration_results['successful_registrations']} agents"
        )
        
        # Perform initial health checks
        health_results = registry.perform_health_checks()
        logger.info(
            f"Initial health check: {health_results['healthy_agents']} healthy, "
            f"{health_results['unhealthy_agents']} unhealthy"
        )
    else:
        logger.error("Failed to register any agents - system initialization failed")
        raise RuntimeError("Agent system initialization failed")
    
    return registry


def create_demo_task_assignment() -> Dict[str, Any]:
    logger.info("Creating demo task assignment...")
    
    # Initialize the system
    registry = initialize_agent_system()
    
    # Create sample tasks for each agent type
    demo_tasks = [
        {
            "task_type": "text_analysis",
            "parameters": {
                "text": "This is a sample text for analysis. It contains multiple sentences and should be summarized effectively.",
                "analysis_type": "summarize"
            },
            "description": "Summarize the provided text"
        },
        {
            "task_type": "api_request", 
            "parameters": {
                "url": "https://httpbin.org/json",
                "method": "GET"
            },
            "description": "Fetch JSON data from test API"
        },
        {
            "task_type": "data_processing",
            "parameters": {
                "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operation": "calculate_statistics"
            },
            "description": "Calculate statistics for numerical data"
        }
    ]
    
    results = {
        "demo_completed": True,
        "agents_registered": len(registry.get_registered_agents()),
        "tasks_demonstrated": len(demo_tasks),
        "agent_capabilities": {}
    }
    
    # Document agent capabilities
    for agent_id, agent in registry.get_registered_agents().items():
        results["agent_capabilities"][agent_id] = {
            "name": agent.name,
            "type": agent.agent_state.agent_type,
            "capabilities": [cap.value for cap in agent.capabilities]
        }
    
    logger.info(f"Demo completed with {len(registry.get_registered_agents())} active agents")
    
    return results


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    try:
        demo_results = create_demo_task_assignment()
        print("Agent Integration Demo Results:")
        print(f"- Agents registered: {demo_results['agents_registered']}")
        print(f"- Tasks demonstrated: {demo_results['tasks_demonstrated']}")
        print("\nAgent Capabilities:")
        for agent_id, info in demo_results['agent_capabilities'].items():
            print(f"  {info['name']} ({info['type']}): {', '.join(info['capabilities'])}")
            
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise
