"""
Prompt template models for the AI Agentic Framework
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class PromptTemplate(BaseModel):
    """Prompt template definition"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    version: str = Field(default="1.0.0")
    language: str = Field(default="en", description="Template language")
    
    # Template content
    template: str = Field(..., description="Template string with {variables}")
    system_message: Optional[str] = Field(default=None, description="System message prefix")
    
    # Variables
    variables: List[str] = Field(default_factory=list, description="Required variables")
    optional_variables: List[str] = Field(default_factory=list, description="Optional variables")
    
    # Metadata and performance
    category: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)
    performance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    usage_count: int = Field(default=0, ge=0)
    
    # Author info
    created_by: str = Field(default="system")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Examples
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example inputs/outputs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "customer_support_greeting",
                "name": "Customer Support Greeting",
                "description": "Initial greeting template for customer support",
                "template": "You are a helpful customer support agent.\n\nContext: {context}\n\nUser: {user_input}\n\nAssistant:",
                "variables": ["context", "user_input"],
                "category": "support"
            }
        }
    
    @validator('template')
    def validate_template(cls, v, values):
        """Validate that template contains all declared variables"""
        if 'variables' in values:
            pattern = r'\{(\w+)\}'
            found_vars = set(re.findall(pattern, v))
            declared_vars = set(values['variables'])
            
            missing = declared_vars - found_vars
            if missing:
                raise ValueError(f"Template missing declared variables: {missing}")
        
        return v
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render template with provided context"""
        # Check for required variables
        missing = set(self.variables) - set(context.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Fill in optional variables with empty strings if not provided
        for var in self.optional_variables:
            if var not in context:
                context[var] = ""
        
        # Render template
        try:
            rendered = self.template.format(**context)
            
            # Add system message if present
            if self.system_message:
                rendered = f"{self.system_message}\n\n{rendered}"
            
            return rendered
        except KeyError as e:
            raise ValueError(f"Template variable not provided: {e}")
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
    
    def update_performance(self, score: float):
        """Update performance score (running average)"""
        if self.usage_count == 0:
            self.performance_score = score
        else:
            # Running average
            self.performance_score = (
                (self.performance_score * self.usage_count + score) / 
                (self.usage_count + 1)
            )


class PromptGenerationRequest(BaseModel):
    """Request for dynamic prompt generation"""
    template_id: str
    context: Dict[str, Any]
    user_input: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    rag_context: Optional[str] = None
    max_history_messages: int = Field(default=10, ge=0)
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get full context including history and RAG"""
        full_context = dict(self.context)
        full_context['user_input'] = self.user_input
        
        # Add conversation history
        if self.conversation_history:
            history_str = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in self.conversation_history[-self.max_history_messages:]
            ])
            full_context['history'] = history_str
        else:
            full_context['history'] = ""
        
        # Add RAG context
        if self.rag_context:
            full_context['rag_context'] = self.rag_context
        else:
            full_context['rag_context'] = ""
        
        return full_context


class PromptOptimizationResult(BaseModel):
    """Result of prompt optimization"""
    original_template_id: str
    optimized_template: str
    improvements: List[str] = Field(default_factory=list)
    expected_performance_gain: float = 0.0
    tested: bool = False
    test_results: Optional[Dict[str, Any]] = None
