"""
Lead Conversion State Machine Models

Simplified models for demonstrating Agno workflow state machine
for Brazilian accounting services lead conversion.
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ConversationStage(str, Enum):
    """Conversation stages aligned with the Agilize onboarding journey."""

    INICIAL = "inicial"
    CONFIRMACAO_INICIAL = "confirmacao_inicial"
    QUALIFICACAO = "qualificacao"
    PROPOSTA = "proposta"
    CONTRATACAO = "contratacao"
    COLETA_DOCUMENTOS_PESSOAIS = "coleta_documentos_pessoais"
    DEFINICAO_EMPRESA = "definicao_empresa"
    ESCOLHA_CNAE = "escolha_cnae"
    ENDERECO_COMERCIAL = "endereco_comercial"
    REVISAO_FINAL = "revisao_final"
    PROCESSAMENTO = "processamento"
    CONCLUIDO = "concluido"
    PAUSADO = "pausado"
    ABANDONADO = "abandonado"


class LeadData(BaseModel):
    """Lead information model with Brazilian context."""
    nome_completo: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    telefone: Optional[str] = None
    empresa: Optional[str] = Field(None, min_length=2, max_length=200)
    cargo: Optional[str] = Field(None, max_length=100)

    # Qualification fields for Brazilian accounting services
    renda_mensal: Optional[float] = Field(None, ge=0, description="Renda mensal em R$")
    tem_empresa: Optional[bool] = None
    precisa_contabilidade: Optional[bool] = None
    tipo_interesse: Optional[str] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[str] = None

    @validator('telefone')
    def validate_telefone_brasileiro(cls, v):
        if v is None:
            return v
        # Brazilian phone validation - accepts various formats
        telefone_limpo = re.sub(r'\D', '', v)
        if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        return v

    @validator('renda_mensal')
    def validate_renda_positiva(cls, v):
        if v is not None and v < 0:
            raise ValueError('Renda mensal deve ser positiva')
        return v


class ConversationContext(BaseModel):
    """Complete conversation state management."""
    stage: ConversationStage = ConversationStage.INICIAL
    lead_data: LeadData = Field(default_factory=LeadData)

    # Journey specific blocks
    initial_confirmation: Dict[str, Any] = Field(default_factory=dict)
    business_profile: Dict[str, Any] = Field(default_factory=dict)
    proposal_status: Dict[str, Any] = Field(default_factory=dict)
    contract_data: Dict[str, Any] = Field(default_factory=dict)
    document_status: Dict[str, Any] = Field(default_factory=dict)
    company_profile: Dict[str, Any] = Field(default_factory=dict)
    review_status: Dict[str, Any] = Field(default_factory=dict)
    process_status: Dict[str, Any] = Field(default_factory=dict)

    # Conversation tracking
    conversation_turns: int = 0
    messages_exchanged: List[Dict[str, str]] = Field(default_factory=list)

    # Qualification tracking
    is_qualified: bool = False
    qualification_reason: Optional[str] = None

    # Field collection tracking
    fields_collected: List[str] = Field(default_factory=list)
    validation_attempts: Dict[str, int] = Field(default_factory=dict)

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    last_interaction_at: datetime = Field(default_factory=datetime.now)

    def is_session_expired(self, timeout_hours: int = 24) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_interaction_at + timedelta(hours=timeout_hours)
        return datetime.now() > expiry_time

    def check_qualification(self) -> bool:
        """Check if lead is qualified (renda >= R$5,000)."""
        renda = self.lead_data.renda_mensal
        if renda is None:
            return False

        if renda >= 5000:
            self.is_qualified = True
            self.qualification_reason = (
                f"Qualificado: renda mensal de R${renda:,.2f}"
            )
            return True

        self.is_qualified = False
        self.qualification_reason = (
            f"Não qualificado: renda mensal de R${renda:,.2f} (mínimo R$5.000)"
        )
        return False


class AgentResponse(BaseModel):
    """Standard response format for all agents."""
    message: str = Field(..., description="Response message in Portuguese")
    next_stage: ConversationStage = Field(..., description="Recommended next stage")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence in decision")
    field_extracted: Optional[str] = Field(None, description="Field name if data was extracted")
    field_value: Optional[str] = Field(None, description="Field value if data was extracted")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for state persistence")
    user_id: Optional[str] = Field(None, description="User ID for cross-channel state")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str
    responses: List[str]
    stage: str
    qualified: Optional[bool] = None
    qualification_reason: Optional[str] = None
    context: Dict = Field(default_factory=dict)
