"""
PRD (Product Requirements Document) Generation Workflow

This module implements a conversational workflow that guides stakeholders
through the process of creating comprehensive Product Requirements Documents
for software products.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.workflow import Workflow, Step

from app.core.database import get_agent_storage, get_workflow_storage
from app.models.prd_models import ConversationContext, PRDPhase, ProductData, PRDGenerationStatus

logger = logging.getLogger(__name__)

# Ordered flow of PRD generation phases
PRD_PHASE_SEQUENCE: List[PRDPhase] = [
    PRDPhase.INITIAL_DISCOVERY,
    PRDPhase.PRODUCT_VISION,
    PRDPhase.TARGET_AUDIENCE,
    PRDPhase.CORE_FEATURES,
    PRDPhase.USER_STORIES,
    PRDPhase.TECHNICAL_REQUIREMENTS,
    PRDPhase.SUCCESS_METRICS,
    PRDPhase.CONSTRAINTS_ASSUMPTIONS,
    PRDPhase.PRD_REVIEW,
    PRDPhase.PRD_REFINEMENT,
    PRDPhase.PRD_FINALIZATION,
    PRDPhase.COMPLETED,
]


def get_prd_generation_workflow(session_id: Optional[str] = None, user_id: Optional[str] = None) -> "PRDGenerationWorkflow":
    """Factory function to create PRD generation workflow instances."""
    return PRDGenerationWorkflow(session_id=session_id, user_id=user_id)


class PRDGenerationWorkflow(Workflow):
    """
    PRD Generation Workflow that guides users through creating comprehensive
    Product Requirements Documents through conversational interactions.
    """

    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None, **kwargs):
        self._context: Optional[ConversationContext] = None
        self._session_id = session_id or f"prd_{uuid.uuid4().hex[:8]}"
        self._user_id = user_id
        self._agent_storage = get_agent_storage()
        self._workflow_storage = get_workflow_storage()

        # Initialize the main PRD agent
        self._agent = self._init_agent()

        super().__init__(
            name="PRD Generation Workflow",
            description="Conversational workflow for creating Product Requirements Documents",
            steps=[
                Step(
                    name="PRD Generation",
                    agent=self._agent,
                    description="Generate PRD through conversational interaction"
                )
            ],
            **kwargs,
        )

    def _init_agent(self) -> Agent:
        """Initialize the main PRD generation agent."""

        # Get OpenRouter configuration
        import os
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        openrouter_model = os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash')

        if not openrouter_token:
            raise ValueError("OPENROUTER_TOKEN environment variable is required")

        # Create the main PRD agent with comprehensive instructions
        instructions = [
            "You are an expert Product Manager with 10+ years of experience creating PRDs for successful software products.",
            "Your mission is to guide stakeholders through creating comprehensive Product Requirements Documents.",
            "You are professional, curious, methodical, and encouraging.",
            "",
            "IMPORTANT: You must communicate with users ONLY in Brazilian Portuguese. All your responses, questions, and explanations should be in Portuguese (Brazil).",
            "",
            "CONVERSATION FLOW:",
            "1. Initial Discovery - Understand the product concept and problem",
            "2. Product Vision - Define long-term vision and business goals",
            "3. Target Audience - Create detailed user personas",
            "4. Core Features - Define essential functionality",
            "5. User Stories - Create detailed user scenarios",
            "6. Technical Requirements - Gather technical constraints",
            "7. Success Metrics - Define measurable KPIs",
            "8. Constraints & Assumptions - Document limitations",
            "9. PRD Review - Present comprehensive summary",
            "10. PRD Refinement - Make requested changes",
            "11. PRD Finalization - Deliver final document",
            "",
            "GUIDELINES:",
            "- Always communicate in Brazilian Portuguese",
            "- Always ask thoughtful follow-up questions",
            "- Be specific and detailed in your responses",
            "- Guide the conversation naturally through the phases",
            "- Gather comprehensive information before moving to next phase",
            "- Create actionable, detailed requirements",
            "- End each response with a specific question to continue the conversation",
            "- Use Brazilian Portuguese terminology and expressions naturally"
        ]

        return Agent(
            name="PRD_Generation_Agent",
            model=OpenRouter(id=openrouter_model, api_key=openrouter_token),
            instructions=instructions,
            add_history_to_context=True,
            num_history_runs=10,
            add_datetime_to_context=True,
            session_id=self._session_id,
        )

    def get_context(self) -> Optional[ConversationContext]:
        """Get current conversation context."""
        return self._ensure_context()

    def get_completion_percentage(self) -> int:
        """Calculate completion percentage based on gathered information."""
        context = self._ensure_context()
        if not context:
            return 0

        # Simple completion calculation based on filled fields
        total_fields = 10
        completed_fields = 0

        product_data = context.product_data
        if product_data.product_name:
            completed_fields += 1
        if product_data.product_vision:
            completed_fields += 1
        if product_data.user_personas:
            completed_fields += 1
        if product_data.core_features:
            completed_fields += 1
        if product_data.user_stories:
            completed_fields += 1
        if product_data.technical_requirements:
            completed_fields += 1
        if product_data.success_metrics:
            completed_fields += 1
        if product_data.budget_constraints or product_data.timeline_constraints:
            completed_fields += 1
        if context.generated_prd:
            completed_fields += 1
        if context.prd_approved:
            completed_fields += 1

        return min(int((completed_fields / total_fields) * 100), 100)

    def _ensure_context(self) -> ConversationContext:
        """Ensure conversation context exists and is properly initialized."""

        if self._context is None:
            # Create new context (no persistent storage available)
            self._context = ConversationContext(
                session_id=self._session_id,
                user_id=self._user_id,
                phase=PRDPhase.INITIAL_DISCOVERY,
            )

        return self._context

    def _store_context(self):
        """Update conversation context (in-memory only)."""

        if self._context:
            self._context.updated_at = datetime.now()
            self._context.total_interactions += 1

    def run(self, message: str):
        """Run the PRD generation workflow with the given message."""

        # Ensure context exists
        context = self._ensure_context()

        # Store the context after processing
        self._store_context()

        # Run the workflow with the message
        return super().run(message)
