"""
Prompt Manager - Manages prompt templates and dynamic generation
"""
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..models import PromptTemplate, PromptGenerationRequest, PromptOptimizationResult


logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates and dynamic prompt generation"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        logger.info("PromptManager initialized")
    
    def _load_default_templates(self):
        """Load default prompt templates"""
        # General assistant template
        general_template = PromptTemplate(
            template_id="general_assistant",
            name="General Assistant",
            description="General purpose assistant template",
            template="You are {agent_name}, a helpful AI assistant. {agent_description}\n\nContext:\n{rag_context}\n\nConversation History:\n{history}\n\nUser: {user_input}\n\nAssistant:",
            variables=["agent_name", "agent_description", "rag_context", "history", "user_input"],
            category="general"
        )
        self.register_template(general_template)
        
        # Customer support template
        support_template = PromptTemplate(
            template_id="customer_support",
            name="Customer Support",
            description="Template for customer support agents",
            template="You are {agent_name}, a professional customer support representative. {agent_description}\n\nRelevant Information:\n{rag_context}\n\nPrevious Conversation:\n{history}\n\nCustomer Query: {user_input}\n\nProvide a helpful, empathetic, and professional response:",
            variables=["agent_name", "agent_description", "rag_context", "history", "user_input"],
            category="support"
        )
        self.register_template(support_template)
        
        # Research assistant template
        research_template = PromptTemplate(
            template_id="research_assistant",
            name="Research Assistant",
            description="Template for research and analysis tasks",
            template="You are {agent_name}, a thorough research assistant. {agent_description}\n\nResearch Context:\n{rag_context}\n\nConversation History:\n{history}\n\nResearch Query: {user_input}\n\nProvide a comprehensive, well-researched response with sources when possible:",
            variables=["agent_name", "agent_description", "rag_context", "history", "user_input"],
            category="research"
        )
        self.register_template(research_template)
    
    def register_template(self, template: PromptTemplate):
        """Register a new prompt template"""
        if template.template_id in self.templates:
            logger.warning(f"Template {template.template_id} already exists, overwriting")
        
        self.templates[template.template_id] = template
        logger.info(f"Registered prompt template: {template.name} ({template.template_id})")
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """List all templates, optionally filtered by category"""
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())
    
    async def generate_prompt(
        self,
        template_id: str,
        context: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
        max_history: int = 10
    ) -> str:
        """Generate a prompt from template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Format conversation history
        if history and 'history' not in context:
            history_str = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in history[-max_history:]
            ])
            context['history'] = history_str
        elif 'history' not in context:
            context['history'] = ""
        
        # Ensure all required variables have defaults
        if 'rag_context' not in context:
            context['rag_context'] = ""
        
        # Render template
        try:
            prompt = template.render(context)
            template.increment_usage()
            return prompt
        except Exception as e:
            logger.error(f"Failed to generate prompt: {e}")
            raise
    
    def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        template: str,
        variables: List[str],
        category: str = "custom"
    ) -> PromptTemplate:
        """Create a new prompt template"""
        prompt_template = PromptTemplate(
            template_id=template_id,
            name=name,
            description=description,
            template=template,
            variables=variables,
            category=category
        )
        
        self.register_template(prompt_template)
        return prompt_template
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> PromptTemplate:
        """Update an existing template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        return template
    
    def delete_template(self, template_id: str):
        """Delete a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Deleted template: {template_id}")
    
    async def optimize_template(
        self,
        template_id: str,
        feedback: List[Dict[str, Any]]
    ) -> PromptOptimizationResult:
        """Optimize a template based on feedback"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Simple optimization based on feedback
        # In production, use LLM-based optimization
        improvements = []
        optimized_template = template.template
        
        # Analyze feedback
        avg_score = sum(f.get('score', 0) for f in feedback) / max(len(feedback), 1)
        
        if avg_score < 0.7:
            improvements.append("Consider adding more context or examples")
            improvements.append("Simplify language and instructions")
        
        return PromptOptimizationResult(
            original_template_id=template_id,
            optimized_template=optimized_template,
            improvements=improvements,
            expected_performance_gain=0.1 if avg_score < 0.7 else 0.0,
            tested=False
        )
    
    def get_template_performance(self, template_id: str) -> Dict[str, Any]:
        """Get performance metrics for a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return {
            "template_id": template_id,
            "usage_count": template.usage_count,
            "performance_score": template.performance_score,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }