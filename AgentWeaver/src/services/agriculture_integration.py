"""
Agriculture Integration Service
Integrates the agriculture router and agents with the existing AgentWeaver infrastructure.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..orchestration.supervisor import SupervisorNode
from ..agents.agriculture_router import AgricultureRouter, create_agriculture_router
from ..core.agriculture_models import (
    AgricultureQuery, AgricultureTask, QueryDomain, Language,
    AgricultureCapability, AggregatedResponse, AgentResponse
)
from ..core.models import Task, TaskPriority, TaskStatus, AgentState, AgentStatus
from ..services.websocket_integration import integration_service


logger = logging.getLogger(__name__)


class AgricultureIntegrationService:
    """
    Service that integrates agricultural capabilities with AgentWeaver.
    Handles query processing, agent coordination, and response aggregation.
    """
    
    def __init__(self, supervisor: SupervisorNode):
        self.supervisor = supervisor
        self.agriculture_router: Optional[AgricultureRouter] = None
        self.specialist_agents: Dict[str, Any] = {}
        self.active_queries: Dict[str, Dict[str, Any]] = {}
        
        # Initialize router
        self._initialize_router()
        
        # Register with integration service for WebSocket updates
        integration_service.register_handler("agriculture_query", self.handle_agriculture_query)
        integration_service.register_handler("get_agriculture_status", self.get_status)
    
    def _initialize_router(self):
        """Initialize the agriculture router"""
        try:
            self.agriculture_router = create_agriculture_router()
            
            # Register router with supervisor
            self.supervisor.register_agent(self.agriculture_router.agent_state)
            
            logger.info("Agriculture router initialized and registered")
            
        except Exception as e:
            logger.error(f"Failed to initialize agriculture router: {e}")
    
    def register_specialist_agent(self, agent_id: str, agent_instance: Any, domains: List[QueryDomain]):
        """Register a specialist agricultural agent"""
        try:
            self.specialist_agents[agent_id] = {
                "instance": agent_instance,
                "domains": domains,
                "status": "active"
            }
            
            # Register with supervisor
            if hasattr(agent_instance, "agent_state"):
                self.supervisor.register_agent(agent_instance.agent_state)
            
            # Update router registry
            if self.agriculture_router:
                for domain in domains:
                    if domain not in self.agriculture_router.agent_registry:
                        self.agriculture_router.agent_registry[domain] = []
                    if agent_id not in self.agriculture_router.agent_registry[domain]:
                        self.agriculture_router.agent_registry[domain].append(agent_id)
            
            logger.info(f"Registered specialist agent {agent_id} for domains: {domains}")
            
        except Exception as e:
            logger.error(f"Failed to register specialist agent {agent_id}: {e}")
    
    async def handle_agriculture_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for handling agricultural queries.
        Processes through router and coordinates specialist agents.
        """
        try:
            # Create AgricultureQuery object
            agriculture_query = AgricultureQuery(**query_data)
            
            logger.info(f"Processing agriculture query: {agriculture_query.query_id}")
            
            # Store query for tracking
            self.active_queries[agriculture_query.query_id] = {
                "query": agriculture_query,
                "start_time": datetime.now(),
                "status": "processing",
                "responses": {}
            }
            
            # Send status update via WebSocket
            await self._send_status_update(agriculture_query.query_id, "processing", "Analyzing query...")
            
            # Step 1: Route query using agriculture router
            routing_result = await self._route_query(agriculture_query)
            
            if not routing_result or "error" in routing_result:
                error_msg = routing_result.get("error", "Routing failed") if routing_result else "Router not available"
                await self._send_status_update(agriculture_query.query_id, "error", error_msg)
                return {"error": error_msg}
            
            routing_decision = routing_result["routing_decision"]
            
            # Check if clarification is needed
            if routing_decision.requires_clarification:
                await self._send_status_update(
                    agriculture_query.query_id, 
                    "clarification_needed",
                    "Need more information",
                    {"questions": routing_decision.clarification_questions}
                )
                return {
                    "status": "clarification_needed",
                    "questions": routing_decision.clarification_questions,
                    "query_id": agriculture_query.query_id
                }
            
            # Step 2: Execute selected agents
            agent_responses = await self._execute_specialist_agents(
                agriculture_query, routing_decision
            )
            
            # Step 3: Aggregate responses
            final_response = await self._aggregate_responses(
                agriculture_query, routing_decision, agent_responses
            )
            
            # Update query status
            self.active_queries[agriculture_query.query_id]["status"] = "completed"
            self.active_queries[agriculture_query.query_id]["final_response"] = final_response
            
            # Send final update
            await self._send_status_update(
                agriculture_query.query_id, 
                "completed", 
                "Query processed successfully",
                {"response": final_response.dict()}
            )
            
            logger.info(f"Completed agriculture query: {agriculture_query.query_id}")
            
            return {
                "status": "success",
                "query_id": agriculture_query.query_id,
                "response": final_response.dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to handle agriculture query: {e}")
            
            if "query_id" in locals():
                await self._send_status_update(agriculture_query.query_id, "error", str(e))
                if agriculture_query.query_id in self.active_queries:
                    self.active_queries[agriculture_query.query_id]["status"] = "error"
            
            return {"error": str(e)}
    
    async def _route_query(self, agriculture_query: AgricultureQuery) -> Optional[Dict[str, Any]]:
        """Route query using agriculture router"""
        if not self.agriculture_router:
            return {"error": "Agriculture router not initialized"}
        
        try:
            # Create routing task
            routing_task = AgricultureTask(
                task_id=f"route_{agriculture_query.query_id}",
                description=agriculture_query.query_text,
                task_type="routing",
                priority=agriculture_query.priority,
                required_capabilities=[AgricultureCapability.QUERY_ROUTING],
                query_data=agriculture_query
            )
            
            # Execute routing
            result = await self.agriculture_router.execute(routing_task, agriculture_query.context)
            return result
            
        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            return {"error": str(e)}
    
    async def _execute_specialist_agents(
        self, 
        agriculture_query: AgricultureQuery, 
        routing_decision
    ) -> List[AgentResponse]:
        """Execute the selected specialist agents"""
        
        agent_responses = []
        selected_agents = routing_decision.selected_agents
        
        if not selected_agents:
            logger.warning("No agents selected for query")
            return agent_responses
        
        try:
            if routing_decision.execution_plan == "parallel":
                # Execute agents in parallel
                tasks = []
                for agent_id in selected_agents:
                    if agent_id in self.specialist_agents:
                        task = self._execute_single_agent(agent_id, agriculture_query)
                        tasks.append(task)
                
                if tasks:
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    for response in responses:
                        if isinstance(response, AgentResponse):
                            agent_responses.append(response)
                        elif isinstance(response, Exception):
                            logger.error(f"Agent execution failed: {response}")
            
            else:
                # Execute agents sequentially
                for agent_id in selected_agents:
                    if agent_id in self.specialist_agents:
                        try:
                            response = await self._execute_single_agent(agent_id, agriculture_query)
                            if response:
                                agent_responses.append(response)
                        except Exception as e:
                            logger.error(f"Failed to execute agent {agent_id}: {e}")
            
            logger.info(f"Executed {len(agent_responses)} agents successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute specialist agents: {e}")
        
        return agent_responses
    
    async def _execute_single_agent(self, agent_id: str, agriculture_query: AgricultureQuery) -> Optional[AgentResponse]:
        """Execute a single specialist agent"""
        
        if agent_id not in self.specialist_agents:
            logger.warning(f"Agent {agent_id} not found")
            return None
        
        try:
            agent_info = self.specialist_agents[agent_id]
            agent_instance = agent_info["instance"]
            
            # Create task for the agent
            agent_task = AgricultureTask(
                task_id=f"{agent_id}_{agriculture_query.query_id}",
                description=agriculture_query.query_text,
                task_type="agriculture_analysis",
                priority=agriculture_query.priority,
                query_data=agriculture_query
            )
            
            # Execute agent
            start_time = datetime.now()
            result = await agent_instance.execute(agent_task, agriculture_query.context)
            end_time = datetime.now()
            
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            # Convert result to AgentResponse
            if isinstance(result, dict) and "response" in result:
                response = AgentResponse(
                    agent_id=agent_id,
                    agent_name=getattr(agent_instance, "name", agent_id),
                    query_id=agriculture_query.query_id,
                    response_text=result["response"],
                    confidence_score=result.get("confidence", 0.8),
                    reasoning=result.get("reasoning", ""),
                    sources=result.get("sources", []),
                    recommendations=result.get("recommendations", []),
                    warnings=result.get("warnings", []),
                    processing_time_ms=processing_time,
                    metadata=result.get("metadata", {})
                )
                return response
            
        except Exception as e:
            logger.error(f"Failed to execute agent {agent_id}: {e}")
        
        return None
    
    async def _aggregate_responses(
        self, 
        agriculture_query: AgricultureQuery, 
        routing_decision, 
        agent_responses: List[AgentResponse]
    ) -> AggregatedResponse:
        """Aggregate responses from multiple agents into final response"""
        
        try:
            if not agent_responses:
                final_text = "I'm sorry, I couldn't process your query at the moment. Please try rephrasing your question or contact support."
                confidence = 0.1
            
            elif len(agent_responses) == 1:
                # Single agent response
                response = agent_responses[0]
                final_text = response.response_text
                confidence = response.confidence_score
            
            else:
                # Multiple agent responses - create comprehensive answer
                final_text = self._synthesize_multi_agent_response(agent_responses)
                confidence = sum(r.confidence_score for r in agent_responses) / len(agent_responses)
            
            # Calculate total processing time
            total_processing_time = sum(r.processing_time_ms or 0 for r in agent_responses)
            
            aggregated_response = AggregatedResponse(
                query_id=agriculture_query.query_id,
                original_query=agriculture_query.query_text,
                detected_domains=routing_decision.detected_domains,
                agent_responses=agent_responses,
                final_response=final_text,
                confidence_score=min(confidence, 1.0),
                response_language=agriculture_query.query_language,
                processing_summary={
                    "agents_used": len(agent_responses),
                    "execution_plan": routing_decision.execution_plan,
                    "routing_confidence": routing_decision.confidence
                },
                total_processing_time_ms=total_processing_time
            )
            
            return aggregated_response
            
        except Exception as e:
            logger.error(f"Failed to aggregate responses: {e}")
            
            # Return error response
            return AggregatedResponse(
                query_id=agriculture_query.query_id,
                original_query=agriculture_query.query_text,
                detected_domains=[],
                agent_responses=[],
                final_response=f"Error processing query: {str(e)}",
                confidence_score=0.0,
                total_processing_time_ms=0
            )
    
    def _synthesize_multi_agent_response(self, agent_responses: List[AgentResponse]) -> str:
        """Synthesize responses from multiple agents into coherent answer"""
        
        synthesis = []
        
        # Group by response type/domain
        domain_responses = {}
        for response in agent_responses:
            agent_name = response.agent_name
            domain_responses[agent_name] = response.response_text
        
        # Create structured response
        synthesis.append("Based on my analysis, here's what I recommend:\n")
        
        for i, (agent_name, response_text) in enumerate(domain_responses.items(), 1):
            synthesis.append(f"{i}. **{agent_name}**: {response_text}")
        
        # Add confidence note if low
        avg_confidence = sum(r.confidence_score for r in agent_responses) / len(agent_responses)
        if avg_confidence < 0.7:
            synthesis.append("\n*Note: This recommendation has moderate confidence. Consider consulting local agricultural experts for verification.*")
        
        return "\n\n".join(synthesis)
    
    async def _send_status_update(self, query_id: str, status: str, message: str, data: Optional[Dict] = None):
        """Send status update via WebSocket"""
        try:
            update_data = {
                "type": "agriculture_query_update",
                "query_id": query_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            if data:
                update_data.update(data)
            
            await integration_service.broadcast_update("agriculture", update_data)
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def get_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of agriculture system"""
        try:
            return {
                "status": "active",
                "router_available": self.agriculture_router is not None,
                "specialist_agents": len(self.specialist_agents),
                "active_queries": len(self.active_queries),
                "agent_details": {
                    agent_id: {
                        "domains": [d.value for d in info["domains"]],
                        "status": info["status"]
                    }
                    for agent_id, info in self.specialist_agents.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get agriculture status: {e}")
            return {"error": str(e)}
    
    def get_query_status(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific query"""
        return self.active_queries.get(query_id)
    
    def cleanup_completed_queries(self, max_age_hours: int = 24):
        """Clean up old completed queries"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            queries_to_remove = []
            for query_id, query_info in self.active_queries.items():
                if query_info["start_time"] < cutoff_time and query_info["status"] in ["completed", "error"]:
                    queries_to_remove.append(query_id)
            
            for query_id in queries_to_remove:
                del self.active_queries[query_id]
            
            if queries_to_remove:
                logger.info(f"Cleaned up {len(queries_to_remove)} old queries")
                
        except Exception as e:
            logger.error(f"Failed to cleanup queries: {e}")


# Global instance
agriculture_service: Optional[AgricultureIntegrationService] = None


def initialize_agriculture_service(supervisor: SupervisorNode) -> AgricultureIntegrationService:
    """Initialize the global agriculture service"""
    global agriculture_service
    agriculture_service = AgricultureIntegrationService(supervisor)
    return agriculture_service


def get_agriculture_service() -> Optional[AgricultureIntegrationService]:
    """Get the global agriculture service instance"""
    return agriculture_service
