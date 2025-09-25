"""
PRD (Product Requirements Document) Generation Models

Data models for capturing product requirements, user stories, 
technical specifications, and other PRD components.
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PRDPhase(str, Enum):
    """PRD generation conversation phases."""
    
    INITIAL_DISCOVERY = "initial_discovery"
    PRODUCT_VISION = "product_vision"
    TARGET_AUDIENCE = "target_audience"
    CORE_FEATURES = "core_features"
    USER_STORIES = "user_stories"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    SUCCESS_METRICS = "success_metrics"
    CONSTRAINTS_ASSUMPTIONS = "constraints_assumptions"
    PRD_REVIEW = "prd_review"
    PRD_REFINEMENT = "prd_refinement"
    PRD_FINALIZATION = "prd_finalization"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class ProductType(str, Enum):
    """Types of software products."""
    
    WEB_APPLICATION = "web_application"
    MOBILE_APP = "mobile_app"
    DESKTOP_SOFTWARE = "desktop_software"
    API_SERVICE = "api_service"
    SAAS_PLATFORM = "saas_platform"
    E_COMMERCE = "e_commerce"
    GAME = "game"
    IOT_APPLICATION = "iot_application"
    AI_ML_PRODUCT = "ai_ml_product"
    OTHER = "other"


class UserPersona(BaseModel):
    """User persona model."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    demographics: Optional[str] = Field(None, max_length=300)
    goals: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    technical_proficiency: Optional[str] = Field(None, max_length=100)


class UserStory(BaseModel):
    """User story model."""
    
    id: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    persona: str = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="medium")  # high, medium, low
    acceptance_criteria: List[str] = Field(default_factory=list)
    estimated_effort: Optional[str] = Field(None, max_length=50)


class TechnicalRequirement(BaseModel):
    """Technical requirement model."""
    
    category: str = Field(..., min_length=1, max_length=100)  # e.g., "Performance", "Security", "Scalability"
    requirement: str = Field(..., min_length=10, max_length=500)
    priority: str = Field(default="medium")  # high, medium, low
    rationale: Optional[str] = Field(None, max_length=300)


class SuccessMetric(BaseModel):
    """Success metric/KPI model."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=300)
    target_value: Optional[str] = Field(None, max_length=100)
    measurement_method: Optional[str] = Field(None, max_length=200)


class ProductData(BaseModel):
    """Core product information model."""
    
    # Basic product info
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_type: Optional[ProductType] = None
    product_description: Optional[str] = Field(None, min_length=10, max_length=1000)
    
    # Vision and goals
    product_vision: Optional[str] = Field(None, min_length=10, max_length=500)
    business_goals: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    
    # Target audience
    target_audience_description: Optional[str] = Field(None, min_length=10, max_length=500)
    user_personas: List[UserPersona] = Field(default_factory=list)
    
    # Features and functionality
    core_features: List[str] = Field(default_factory=list)
    nice_to_have_features: List[str] = Field(default_factory=list)
    user_stories: List[UserStory] = Field(default_factory=list)
    
    # Technical aspects
    technical_requirements: List[TechnicalRequirement] = Field(default_factory=list)
    technology_preferences: List[str] = Field(default_factory=list)
    integration_requirements: List[str] = Field(default_factory=list)
    
    # Constraints and assumptions
    budget_constraints: Optional[str] = Field(None, max_length=200)
    timeline_constraints: Optional[str] = Field(None, max_length=200)
    resource_constraints: Optional[str] = Field(None, max_length=200)
    assumptions: List[str] = Field(default_factory=list)
    
    # Success metrics
    success_metrics: List[SuccessMetric] = Field(default_factory=list)
    
    # Stakeholder info
    stakeholder_name: Optional[str] = Field(None, min_length=1, max_length=100)
    stakeholder_role: Optional[str] = Field(None, min_length=1, max_length=100)
    stakeholder_email: Optional[str] = None
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)


class PRDGenerationStatus(BaseModel):
    """PRD generation process status."""
    
    status: str = Field(default="in_progress")  # in_progress, completed, paused, abandoned
    current_phase: Optional[str] = None
    completion_percentage: int = Field(default=0, ge=0, le=100)
    estimated_time_remaining: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Conversation context for PRD generation."""
    
    session_id: str
    user_id: Optional[str] = None
    phase: PRDPhase = PRDPhase.INITIAL_DISCOVERY
    product_data: ProductData = Field(default_factory=ProductData)
    generation_status: PRDGenerationStatus = Field(default_factory=PRDGenerationStatus)
    
    # Conversation metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_interactions: int = Field(default=0)
    
    # Phase completion tracking
    completed_phases: List[str] = Field(default_factory=list)
    current_phase_data: Dict[str, Any] = Field(default_factory=dict)
    
    # PRD generation
    generated_prd: Optional[str] = None
    prd_approved: bool = Field(default=False)
    refinement_requests: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for state persistence")
    user_id: Optional[str] = Field(None, description="User ID for cross-channel state")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str
    responses: List[str]
    phase: str
    completion_percentage: Optional[int] = None
    generated_prd: Optional[str] = None
    context: Dict = Field(default_factory=dict)


class PRDDocument(BaseModel):
    """Final PRD document model."""
    
    # Document metadata
    title: str
    version: str = Field(default="1.0")
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    author: Optional[str] = None
    
    # Product overview
    product_name: str
    product_vision: str
    product_description: str
    business_goals: List[str]
    
    # Target audience
    target_audience: str
    user_personas: List[UserPersona]
    
    # Features and requirements
    core_features: List[str]
    user_stories: List[UserStory]
    technical_requirements: List[TechnicalRequirement]
    
    # Success metrics
    success_metrics: List[SuccessMetric]
    
    # Constraints and assumptions
    constraints: Dict[str, str]  # budget, timeline, resources
    assumptions: List[str]
    
    # Additional sections
    integration_requirements: List[str]
    technology_preferences: List[str]
    
    def to_markdown(self) -> str:
        """Convert PRD to markdown format."""

        md_content = []

        # Header
        md_content.append(f"# Product Requirements Document")
        md_content.append(f"## {self.product_name}")
        md_content.append("")
        md_content.append(f"**Version:** {self.version}")
        md_content.append(f"**Created:** {self.created_date.strftime('%Y-%m-%d')}")
        md_content.append(f"**Last Modified:** {self.last_modified.strftime('%Y-%m-%d')}")
        if self.author:
            md_content.append(f"**Author:** {self.author}")
        md_content.append("")

        # Table of Contents
        md_content.append("## Table of Contents")
        md_content.append("1. [Product Overview](#product-overview)")
        md_content.append("2. [Product Vision](#product-vision)")
        md_content.append("3. [Business Goals](#business-goals)")
        md_content.append("4. [Target Audience](#target-audience)")
        md_content.append("5. [User Personas](#user-personas)")
        md_content.append("6. [Core Features](#core-features)")
        md_content.append("7. [User Stories](#user-stories)")
        md_content.append("8. [Technical Requirements](#technical-requirements)")
        md_content.append("9. [Success Metrics](#success-metrics)")
        md_content.append("10. [Constraints and Assumptions](#constraints-and-assumptions)")
        md_content.append("11. [Integration Requirements](#integration-requirements)")
        md_content.append("12. [Technology Preferences](#technology-preferences)")
        md_content.append("")

        # Product Overview
        md_content.append("## Product Overview")
        md_content.append(self.product_description)
        md_content.append("")

        # Product Vision
        md_content.append("## Product Vision")
        md_content.append(self.product_vision)
        md_content.append("")

        # Business Goals
        md_content.append("## Business Goals")
        for i, goal in enumerate(self.business_goals, 1):
            md_content.append(f"{i}. {goal}")
        md_content.append("")

        # Target Audience
        md_content.append("## Target Audience")
        md_content.append(self.target_audience)
        md_content.append("")

        # User Personas
        md_content.append("## User Personas")
        for persona in self.user_personas:
            md_content.append(f"### {persona.name}")
            md_content.append(f"**Description:** {persona.description}")
            if persona.demographics:
                md_content.append(f"**Demographics:** {persona.demographics}")
            if persona.technical_proficiency:
                md_content.append(f"**Technical Proficiency:** {persona.technical_proficiency}")

            if persona.goals:
                md_content.append("**Goals:**")
                for goal in persona.goals:
                    md_content.append(f"- {goal}")

            if persona.pain_points:
                md_content.append("**Pain Points:**")
                for pain_point in persona.pain_points:
                    md_content.append(f"- {pain_point}")
            md_content.append("")

        # Core Features
        md_content.append("## Core Features")
        for i, feature in enumerate(self.core_features, 1):
            md_content.append(f"{i}. {feature}")
        md_content.append("")

        # User Stories
        md_content.append("## User Stories")
        for story in self.user_stories:
            md_content.append(f"### {story.title}")
            md_content.append(f"**As a** {story.persona}, **I want** {story.description}")
            md_content.append(f"**Priority:** {story.priority}")
            if story.estimated_effort:
                md_content.append(f"**Estimated Effort:** {story.estimated_effort}")

            if story.acceptance_criteria:
                md_content.append("**Acceptance Criteria:**")
                for criteria in story.acceptance_criteria:
                    md_content.append(f"- {criteria}")
            md_content.append("")

        # Technical Requirements
        md_content.append("## Technical Requirements")
        current_category = None
        for req in self.technical_requirements:
            if req.category != current_category:
                current_category = req.category
                md_content.append(f"### {current_category}")

            md_content.append(f"- **{req.requirement}** (Priority: {req.priority})")
            if req.rationale:
                md_content.append(f"  - *Rationale: {req.rationale}*")
        md_content.append("")

        # Success Metrics
        md_content.append("## Success Metrics")
        for metric in self.success_metrics:
            md_content.append(f"### {metric.name}")
            md_content.append(f"**Description:** {metric.description}")
            if metric.target_value:
                md_content.append(f"**Target:** {metric.target_value}")
            if metric.measurement_method:
                md_content.append(f"**Measurement:** {metric.measurement_method}")
            md_content.append("")

        # Constraints and Assumptions
        md_content.append("## Constraints and Assumptions")

        if self.constraints:
            md_content.append("### Constraints")
            for constraint_type, constraint_value in self.constraints.items():
                md_content.append(f"- **{constraint_type.title()}:** {constraint_value}")
            md_content.append("")

        if self.assumptions:
            md_content.append("### Assumptions")
            for assumption in self.assumptions:
                md_content.append(f"- {assumption}")
            md_content.append("")

        # Integration Requirements
        if self.integration_requirements:
            md_content.append("## Integration Requirements")
            for integration in self.integration_requirements:
                md_content.append(f"- {integration}")
            md_content.append("")

        # Technology Preferences
        if self.technology_preferences:
            md_content.append("## Technology Preferences")
            for tech in self.technology_preferences:
                md_content.append(f"- {tech}")
            md_content.append("")

        return "\n".join(md_content)
