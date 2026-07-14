"""
Logging Service - Comprehensive logging and evaluation
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Single log entry"""
    log_id: str
    timestamp: datetime
    agent_id: str
    session_id: Optional[str]
    event_type: str
    data: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class EvaluationResult:
    """Evaluation result for an agent response"""
    response_id: str
    agent_id: str
    timestamp: datetime
    
    # Quality metrics
    quality_score: float  # 0.0 to 1.0
    relevance_score: float
    coherence_score: float
    helpfulness_score: float
    
    # Safety metrics
    hallucination_detected: bool
    policy_violations: List[str]
    pii_detected: bool
    
    # User feedback
    user_satisfaction: Optional[float] = None
    user_feedback: Optional[str] = None
    
    # Metadata
    model_used: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class LoggingService:
    """Comprehensive logging and evaluation service"""
    
    def __init__(self, log_directory: str = "./logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.logs: List[LogEntry] = []
        self.evaluations: Dict[str, EvaluationResult] = {}
        
        logger.info("LoggingService initialized")
    
    def log_event(
        self,
        agent_id: str,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        evaluation: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an event"""
        log_id = f"{agent_id}_{datetime.utcnow().timestamp()}"
        
        entry = LogEntry(
            log_id=log_id,
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            session_id=session_id,
            event_type=event_type,
            data=data,
            evaluation=evaluation,
            metadata={}
        )
        
        self.logs.append(entry)
        
        # Write to file
        self._write_log_entry(entry)
        
        return log_id
    
    def _write_log_entry(self, entry: LogEntry):
        """Write log entry to file"""
        try:
            # Create daily log file
            date_str = entry.timestamp.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"agent_logs_{date_str}.jsonl"
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
    
    def log_interaction(
        self,
        agent_id: str,
        user_input: str,
        agent_response: str,
        tools_used: List[str] = None,
        rag_sources: List[str] = None,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        session_id: Optional[str] = None
    ) -> str:
        """Log an agent interaction"""
        data = {
            "user_input": user_input,
            "agent_response": agent_response,
            "tools_used": tools_used or [],
            "rag_sources_accessed": rag_sources or [],
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "cost_usd": cost
        }
        
        return self.log_event(
            agent_id=agent_id,
            event_type="agent_interaction",
            data=data,
            session_id=session_id
        )
    
    async def evaluate_response(
        self,
        response_id: str,
        agent_id: str,
        user_input: str,
        agent_response: str,
        ground_truth: Optional[str] = None,
        model_used: str = "",
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        cost_usd: float = 0.0
    ) -> EvaluationResult:
        """Evaluate an agent response"""
        
        # Simple rule-based evaluation
        # In production, use LLM-based evaluation (e.g., GPT-4 as judge)
        
        # Quality scores (simplified)
        quality_score = self._calculate_quality_score(agent_response)
        relevance_score = self._calculate_relevance_score(user_input, agent_response)
        coherence_score = self._calculate_coherence_score(agent_response)
        helpfulness_score = quality_score  # Simplified
        
        # Safety checks
        hallucination_detected = self._detect_hallucination(agent_response)
        policy_violations = self._check_policy_violations(agent_response)
        pii_detected = self._detect_pii(agent_response)
        
        result = EvaluationResult(
            response_id=response_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            quality_score=quality_score,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            helpfulness_score=helpfulness_score,
            hallucination_detected=hallucination_detected,
            policy_violations=policy_violations,
            pii_detected=pii_detected,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_usd=cost_usd
        )
        
        self.evaluations[response_id] = result
        
        # Log evaluation
        self.log_event(
            agent_id=agent_id,
            event_type="evaluation",
            data=result.to_dict()
        )
        
        return result
    
    def _calculate_quality_score(self, response: str) -> float:
        """Calculate quality score (simplified)"""
        # Simple heuristics
        if not response or len(response.strip()) == 0:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length check (not too short, not too long)
        if 50 <= len(response) <= 1000:
            score += 0.2
        
        # Has proper punctuation
        if any(p in response for p in '.!?'):
            score += 0.1
        
        # No obvious errors
        if 'error' not in response.lower() and 'sorry' not in response.lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, user_input: str, response: str) -> float:
        """Calculate relevance score (simplified)"""
        # Simple keyword overlap
        user_words = set(user_input.lower().split())
        response_words = set(response.lower().split())
        
        if not user_words:
            return 0.5
        
        overlap = len(user_words & response_words)
        score = min(overlap / len(user_words), 1.0)
        
        return max(score, 0.3)  # Minimum baseline
    
    def _calculate_coherence_score(self, response: str) -> float:
        """Calculate coherence score (simplified)"""
        # Simple coherence checks
        if not response:
            return 0.0
        
        sentences = response.split('.')
        if len(sentences) == 0:
            return 0.5
        
        # Check for reasonable sentence lengths
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if 5 <= avg_sentence_length <= 30:
            return 0.8
        elif 3 <= avg_sentence_length <= 50:
            return 0.6
        else:
            return 0.4
    
    def _detect_hallucination(self, response: str) -> bool:
        """Detect potential hallucinations (simplified)"""
        # In production, use fact-checking or LLM-based detection
        hallucination_indicators = [
            "i made that up",
            "i don't actually know",
            "this is fictional",
            "i cannot verify"
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in hallucination_indicators)
    
    def _check_policy_violations(self, response: str) -> List[str]:
        """Check for policy violations (simplified)"""
        violations = []
        
        response_lower = response.lower()
        
        # Check for harmful content
        harmful_keywords = ['violence', 'hate', 'illegal', 'harmful']
        if any(keyword in response_lower for keyword in harmful_keywords):
            violations.append("potential_harmful_content")
        
        return violations
    
    def _detect_pii(self, text: str) -> bool:
        """Detect PII in text (simplified)"""
        import re
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            return True
        
        # Phone pattern (simple)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, text):
            return True
        
        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, text):
            return True
        
        return False
    
    def get_logs(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Query logs"""
        filtered_logs = self.logs
        
        if agent_id:
            filtered_logs = [log for log in filtered_logs if log.agent_id == agent_id]
        
        if event_type:
            filtered_logs = [log for log in filtered_logs if log.event_type == event_type]
        
        if start_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]
        
        if end_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]
        
        # Sort by timestamp descending
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_logs[:limit]
    
    def generate_report(
        self,
        agent_id: str,
        time_range: tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Generate performance report for an agent"""
        start_date, end_date = time_range
        
        # Get logs for the agent in the time range
        logs = self.get_logs(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Get evaluations
        evals = [
            self.evaluations[log.log_id]
            for log in logs
            if log.log_id in self.evaluations
        ]
        
        # Calculate metrics
        total_interactions = len([log for log in logs if log.event_type == "agent_interaction"])
        
        if evals:
            avg_quality = sum(e.quality_score for e in evals) / len(evals)
            avg_relevance = sum(e.relevance_score for e in evals) / len(evals)
            hallucinations = sum(1 for e in evals if e.hallucination_detected)
            policy_violations_count = sum(len(e.policy_violations) for e in evals)
        else:
            avg_quality = 0.0
            avg_relevance = 0.0
            hallucinations = 0
            policy_violations_count = 0
        
        return {
            "agent_id": agent_id,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_interactions": total_interactions,
            "total_evaluations": len(evals),
            "metrics": {
                "average_quality_score": round(avg_quality, 3),
                "average_relevance_score": round(avg_relevance, 3),
                "hallucinations_detected": hallucinations,
                "policy_violations": policy_violations_count
            }
        }
