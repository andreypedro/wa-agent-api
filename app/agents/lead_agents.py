"""
Lead Conversion Agents

Simple agents for future extensibility. Currently, the main logic
is implemented directly in the workflow for simplicity.
"""

import os
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from app.core.database import get_agent_storage


def create_base_lead_agent(name: str, instructions: list) -> Agent:
    """Create a base agent for lead conversion with common configuration."""
    return Agent(
        name=name,
        model=OpenRouter(
            id=os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash'),
            api_key=os.getenv('OPENROUTER_TOKEN')
        ),
        db=get_agent_storage(),
        instructions=instructions,
        markdown=True,
        add_history_to_context=True,
        num_history_runs=3,
        add_datetime_to_context=True,
        debug_mode=False
    )


def create_greeting_agent() -> Agent:
    """Create agent for greeting and initial engagement."""
    instructions = [
        "Você é uma assistente virtual amigável da Agilize Contabilidade.",
        "Sua função é receber visitantes e identificar interesse em serviços contábeis.",
        "Responda sempre em português brasileiro de forma calorosa e profissional.",
        "Identifique sinais de interesse empresarial e direcione para qualificação.",
    ]
    return create_base_lead_agent("Maria - Recepcionista", instructions)


def create_qualification_agent() -> Agent:
    """Create agent for income qualification."""
    instructions = [
        "Você é uma consultora especializada em qualificação de leads.",
        "Sua função é identificar a renda mensal do prospect.",
        "Trabalhamos com pessoas que têm renda acima de R$ 5.000 mensais.",
        "Seja direta mas empática ao perguntar sobre renda.",
        "Responda sempre em português brasileiro.",
    ]
    return create_base_lead_agent("Ana - Qualificadora", instructions)


def create_data_collection_agent() -> Agent:
    """Create agent for collecting contact information."""
    instructions = [
        "Você é uma especialista em coleta de dados de contato.",
        "Sua função é obter nome completo, email e telefone do prospect qualificado.",
        "Seja eficiente mas amigável na coleta das informações.",
        "Responda sempre em português brasileiro.",
    ]
    return create_base_lead_agent("Carla - Dados", instructions)


def create_objection_handler_agent() -> Agent:
    """Create agent for handling objections."""
    instructions = [
        "Você é uma consultora sênior especializada em resolver objeções.",
        "Trate preocupações sobre preço, tempo e confiança com empatia.",
        "Use argumentos baseados em benefícios concretos dos serviços contábeis.",
        "Responda sempre em português brasileiro.",
    ]
    return create_base_lead_agent("Paula - Consultora", instructions)


def create_conversion_agent() -> Agent:
    """Create agent for closing leads."""
    instructions = [
        "Você é uma especialista em fechamento de vendas.",
        "Sua função é finalizar o processo de conversão do lead qualificado.",
        "Seja confiante e entusiasmada ao confirmar o interesse.",
        "Responda sempre em português brasileiro.",
    ]
    return create_base_lead_agent("Júlia - Fechamento", instructions)


# Agent factory for future use
AGENT_FACTORY = {
    "greeting": create_greeting_agent,
    "qualification": create_qualification_agent,
    "data_collection": create_data_collection_agent,
    "objection_handling": create_objection_handler_agent,
    "conversion": create_conversion_agent,
}
