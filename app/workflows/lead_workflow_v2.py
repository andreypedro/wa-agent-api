"""Compatibility wrapper exposing the v2 state machine."""

from app.workflows.lead_workflow import (
    LeadConversionStateMachine,
    LeadConversionWorkflow,
    get_lead_conversion_workflow,
)


def get_lead_conversion_state_machine(session_id: str | None = None, user_id: str | None = None):
    return LeadConversionWorkflow(session_id=session_id, user_id=user_id)


__all__ = [
    "LeadConversionWorkflow",
    "LeadConversionStateMachine",
    "get_lead_conversion_workflow",
    "get_lead_conversion_state_machine",
]
