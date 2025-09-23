"""
Lead Conversion Workflow (Agilize v2)

Implements the full Agilize onboarding state machine with
LLM-driven routing, persistent context, and stage-specific
agents orchestrated through the Agno Workflow v2 router.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agno.agent import Agent, RunResponse
from agno.models.openrouter import OpenRouter
from agno.workflow.v2.router import Router
from agno.workflow.v2.step import Step
from agno.workflow.v2.steps import Steps
from agno.workflow.v2.types import StepInput, StepOutput
from agno.workflow.v2.workflow import Workflow as WorkflowV2, WorkflowRunResponse

from app.core.database import get_agent_storage, get_workflow_storage
from app.models.lead_models import ConversationContext, ConversationStage

logger = logging.getLogger(__name__)

# Ordered flow of the primary states (excludes special states like PAUSADO/ABANDONADO)
PRIMARY_STAGE_SEQUENCE: List[ConversationStage] = [
    ConversationStage.INICIAL,
    ConversationStage.QUALIFICACAO,
    ConversationStage.PROPOSTA,
    ConversationStage.CONTRATACAO,
    ConversationStage.COLETA_DOCUMENTOS_PESSOAIS,
    ConversationStage.DEFINICAO_EMPRESA,
    ConversationStage.ESCOLHA_CNAE,
    ConversationStage.ENDERECO_COMERCIAL,
    ConversationStage.REVISAO_FINAL,
    ConversationStage.PROCESSAMENTO,
    ConversationStage.CONCLUIDO,
]

# Map extracted field names to context sections/attributes
FIELD_SECTION_MAP: Dict[str, Tuple[str, str]] = {
    # Lead data / client profile
    "nome": ("lead_data", "nome_completo"),
    "nome_cliente": ("lead_data", "nome_completo"),
    "nome_completo": ("lead_data", "nome_completo"),
    "email": ("lead_data", "email"),
    "telefone": ("lead_data", "telefone"),
    "tipo_interesse": ("lead_data", "tipo_interesse"),
    "cpf": ("lead_data", "cpf"),
    "data_nascimento": ("lead_data", "data_nascimento"),
    "renda_mensal": ("lead_data", "renda_mensal"),
    # Business profile
    "tipo_negocio": ("business_profile", "tipo_negocio"),
    "estrutura_societaria": ("business_profile", "estrutura_societaria"),
    "numero_socios": ("business_profile", "numero_socios"),
    "faturamento_mei_ok": ("business_profile", "faturamento_mei_ok"),
    "observacao_qualificacao": ("business_profile", "observacao"),
    # Proposal
    "aceite_proposta": ("proposal_status", "aceite_proposta"),
    "aceite": ("proposal_status", "aceite_proposta"),
    "motivo_objecao": ("proposal_status", "motivo_objecao"),
    "objecao_resolvida": ("proposal_status", "objecao_resolvida"),
    # Contract
    "nome_contrato": ("contract_data", "nome_completo"),
    "cpf_contrato": ("contract_data", "cpf"),
    "email_contrato": ("contract_data", "email"),
    "telefone_contrato": ("contract_data", "telefone"),
    "data_nascimento_contrato": ("contract_data", "data_nascimento"),
    "metodo_assinatura": ("contract_data", "metodo_assinatura"),
    "contrato_assinado": ("contract_data", "contrato_assinado"),
    # Documents
    "rg_frente": ("document_status", "rg_frente"),
    "rg_verso": ("document_status", "rg_verso"),
    "cnh_frente": ("document_status", "rg_frente"),
    "cnh_verso": ("document_status", "rg_verso"),
    "comprovante_residencia": ("document_status", "comprovante_residencia"),
    "titulo_eleitor": ("document_status", "titulo_eleitor"),
    "documento_valido": ("document_status", "documento_valido"),
    # Company definition
    "nome_fantasia": ("company_profile", "nome_fantasia"),
    "razao_social": ("company_profile", "razao_social"),
    "razao_social_sugerida": ("company_profile", "razao_social"),
    "capital_social": ("company_profile", "capital_social"),
    "participacoes": ("company_profile", "participacoes"),
    "participacoes_definidas": ("company_profile", "participacoes_definidas"),
    # CNAE
    "descricao_atividade": ("company_profile", "descricao_atividade"),
    "cnae_principal": ("company_profile", "cnae_principal"),
    "cnae_principal_codigo": ("company_profile", "cnae_principal_codigo"),
    "cnae_principal_descricao": ("company_profile", "cnae_principal_descricao"),
    "cnaes_secundarios": ("company_profile", "cnaes_secundarios"),
    "cnaes_confirmados": ("company_profile", "cnaes_confirmados"),
    # Address
    "endereco_tipo": ("company_profile", "endereco_tipo"),
    "cidade_escritorio_virtual": ("company_profile", "cidade_escritorio_virtual"),
    "aceite_escritorio_virtual": ("company_profile", "aceite_escritorio_virtual"),
    "cep": ("company_profile", "cep"),
    "numero": ("company_profile", "numero"),
    "complemento": ("company_profile", "complemento"),
    "endereco_completo": ("company_profile", "endereco_completo"),
    "endereco_confirmado": ("company_profile", "endereco_confirmado"),
    # Review
    "revisao_confirmada": ("review_status", "confirmado"),
    "precisa_editar": ("review_status", "precisa_editar"),
    "campo_para_editar": ("review_status", "campo_para_editar"),
    # Process
    "processo_status": ("process_status", "status"),
    "processo_etapa": ("process_status", "etapa_atual"),
    "processo_mensagem": ("process_status", "mensagem"),
    "processo_finalizado": ("process_status", "finalizado"),
    "cnpj": ("process_status", "cnpj"),
    "tempo_estimado": ("process_status", "tempo_estimado"),
}


BOOL_KEYS = {
    "faturamento_mei_ok",
    "aceite_proposta",
    "aceite",
    "objecao_resolvida",
    "contrato_assinado",
    "documento_valido",
    "participacoes_definidas",
    "cnaes_confirmados",
    "aceite_escritorio_virtual",
    "endereco_confirmado",
    "revisao_confirmada",
    "precisa_editar",
    "processo_finalizado",
}

INT_KEYS = {"numero_socios"}
FLOAT_KEYS = {"renda_mensal", "capital_social"}

LIST_KEYS = {
    "cnaes_secundarios",
    "participacoes",
}


class LeadConversionWorkflow(WorkflowV2):
    """Router-driven workflow coordinating specialised stage agents."""

    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None, **kwargs):
        self._context: Optional[ConversationContext] = None
        self._latest_user_input: str = ""
        self._agent_storage = get_agent_storage()
        self._agents = self._init_agents(session_id)
        self._stage_steps = self._build_stage_steps()

        router = Router(
            name="conversation_state_router",
            description="Seleciona o agente apropriado para o estágio atual",
            selector=self._route_conversation_state,
            choices=list(self._stage_steps.values()),
        )

        super().__init__(
            name="Agilize Onboarding State Machine",
            description="Fluxo conversacional completo para abertura de empresas",
            steps=[router],
            session_id=session_id,
            user_id=user_id,
            storage=get_workflow_storage(),
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Agent initialisation
    # ------------------------------------------------------------------
    def _init_agents(self, session_id: Optional[str]) -> Dict[ConversationStage, Agent]:
        model = OpenRouter(
            id=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
            api_key=os.getenv("OPENROUTER_TOKEN"),
        )

        base_kwargs = {
            "model": model,
            "storage": self._agent_storage,
            "session_id": session_id,
            "add_history_to_messages": True,
            "markdown": True,
            "debug_mode": False,
        }

        structured_output = self._structured_output_instructions()

        stage_instructions: Dict[ConversationStage, List[str]] = {
            ConversationStage.INICIAL: [
                "Você é 'Maria', assistente virtual da Agilize.",
                "🚨🚨🚨 REGRA INVIOLÁVEL: TODA resposta DEVE terminar com uma pergunta específica.",
                "NUNCA diga apenas 'Que ótimo!' ou 'Perfeito!' sem uma pergunta imediata.",
                "SEMPRE use este formato: [1 frase de saudação] + [pergunta direta]",
                "Se falta nome: 'Olá! Como posso te chamar?'",
                "Se falta interesse: 'Ótimo, [nome]! Você está pensando em abrir sua primeira empresa ou já tem uma?'",
                "Se usuário diz 'quero abrir empresa': 'Que ótimo! Como posso te chamar?'",
                "Se ambos coletados: 'Perfeito! Seu negócio será de comércio, serviços ou indústria?'",
                "JAMAIS termine sem uma pergunta que exija resposta do cliente.",
            ],
            ConversationStage.QUALIFICACAO: [
                "MISSÃO: Coletar tipo de negócio, estrutura societária e validações.",
                "🚨 OBRIGATÓRIO: TODA resposta DEVE terminar com uma pergunta específica.",
                "Se falta tipo_negocio: termine com 'Seu negócio será de comércio, serviços, indústria ou algo misto?'",
                "Se falta estrutura: termine com 'Você pretende abrir como MEI, ter sócios, ou ainda está decidindo?'",
                "Se MEI e falta validação: termine com 'Seu faturamento anual ficará até R$81 mil?'",
                "Se sócios e falta número: termine com 'Quantos sócios serão no total?'",
                "Se tudo coletado: termine com 'Perfeito! Posso apresentar a proposta ideal para você?'",
                "NUNCA termine sem uma pergunta direta que exija resposta do cliente.",
            ],
            ConversationStage.PROPOSTA: [
                "MISSÃO: Apresentar proposta personalizada e obter aceite.",
                "🚨 OBRIGATÓRIO: TODA resposta DEVE terminar com uma pergunta específica.",
                "Monte proposta (MEI ou LTDA) com benefícios (abertura grátis, descontos, prazos).",
                "SEMPRE termine com: 'Aceita seguir com essa proposta?' ou 'Podemos prosseguir com a abertura?'",
                "Se houver objeção: registre motivo e termine com 'Posso esclarecer alguma dúvida específica?'",
                "NUNCA termine sem uma pergunta direta que exija resposta do cliente.",
            ],
            ConversationStage.CONTRATACAO: [
                "MISSÃO: Coletar dados contratuais e obter assinatura.",
                "🚨 OBRIGATÓRIO: TODA resposta DEVE terminar com uma pergunta específica.",
                "Se falta nome: termine com 'Qual é o seu nome completo?'",
                "Se falta CPF: termine com 'Qual é o seu CPF?'",
                "Se falta email: termine com 'Qual é o seu email?'",
                "Se falta telefone: termine com 'Qual é o seu telefone?'",
                "Se falta data nascimento: termine com 'Qual é a sua data de nascimento (DD/MM/AAAA)?'",
                "Se dados completos mas falta método: termine com 'Como prefere assinar o contrato: SMS, email ou WhatsApp?'",
                "Se tudo pronto: termine com 'Confirma a assinatura do contrato?'",
                "NUNCA termine sem uma pergunta direta que exija resposta do cliente.",
            ],
            ConversationStage.COLETA_DOCUMENTOS_PESSOAIS: [
                "Explique os documentos necessários (RG/CNH frente, verso, comprovante residência, título opcional).",
                "Solicite uploads um a um, confirmando nitidez e validade.",
                "SEMPRE termine pedindo o próximo documento específico ou confirmação.",
                "Se falta documento: 'Agora preciso da foto do [documento específico]'. Se completo: 'Perfeito! Vamos definir sua empresa?'",
                "Incentive com dicas caso a foto esteja ruim. Ao concluir, motive o cliente para a etapa de definição da empresa.",
            ],
            ConversationStage.DEFINICAO_EMPRESA: [
                "Celebre: 'vamos criar a identidade da sua empresa'.",
                "Pergunte nome fantasia desejado e gere (ou aceite) uma razão social sugerida (razao_social).",
                "Ajude a definir capital social e, se houver sócios, solicite participações (ex.: 60/40).",
                "SEMPRE termine perguntando pelo próximo dado específico.",
                "Se falta nome: 'Qual será o nome fantasia da sua empresa?' Se falta capital: 'Qual será o capital social inicial?'",
                "Confirme os dados antes de seguir para CNAE.",
            ],
            ConversationStage.ESCOLHA_CNAE: [
                "Peça descrição simples das atividades. Use linguagem acessível ao sugerir CNAEs.",
                "Apresente atividade principal (cnae_principal) e até duas secundárias.",
                "SEMPRE termine perguntando pela escolha específica.",
                "Se falta principal: 'Qual dessas atividades será a principal da sua empresa?' Se falta confirmação: 'Confirma essas atividades?'",
                "Explique impactos e confirme se cnaes_confirmados=True. Pergunte se deseja adicionar mais atividades.",
            ],
            ConversationStage.ENDERECO_COMERCIAL: [
                "Apresente opções (escritório virtual recomendado, residencial, comercial).",
                "Se escolher virtual, ofereça cidades disponíveis e confirme aceite_escritorio_virtual.",
                "Caso contrário, peça CEP, número, complemento e confirme endereço completo.",
                "SEMPRE termine perguntando pela escolha ou dado específico.",
                "Se falta tipo: 'Prefere usar escritório virtual ou seu endereço residencial?' Se falta endereço: 'Qual o CEP do endereço?'",
                "Reforce benefícios e prepare transição para revisão final.",
            ],
            ConversationStage.REVISAO_FINAL: [
                "Monte um resumo organizado de todos os dados coletados.",
                "SEMPRE termine perguntando: 'Está tudo correto? Posso prosseguir com a abertura da sua empresa?'",
                "Caso queira editar algo, registre campo_para_editar e direcione para o estágio correspondente.",
                "Após confirmação, destaque termos e prossiga para PROCESSAMENTO.",
            ],
            ConversationStage.PROCESSAMENTO: [
                "Comunique que o processo de abertura foi iniciado e informe etapas (análise documentação, Junta Comercial, CNPJ etc.).",
                "Atualize process_status com status/etapa/tempo estimado.",
                "SEMPRE termine informando o status atual e próximos passos.",
                "Durante processo: 'Estamos na etapa [X]. Próximo passo: [Y]. Tempo estimado: [Z].'",
                "Ao finalizar, informe CNPJ e próximos passos e defina processo_finalizado=True para avançar a CONCLUIDO.",
            ],
            ConversationStage.CONCLUIDO: [
                "🎉 MISSÃO: Celebrar conclusão e encerrar definitivamente.",
                "⚠️ EXCEÇÃO ÚNICA: Esta é a ÚNICA etapa onde você NÃO faz perguntas.",
                "Celebre: 'Parabéns! Sua empresa está oficialmente aberta!'",
                "Informe CNPJ e próximos passos (emitir nota, app Agilize).",
                "TERMINE OBRIGATORIAMENTE com: 'Este atendimento está CONCLUÍDO. Estarei aqui sempre que precisar!'",
                "NÃO faça perguntas. NÃO ofereça mais serviços. APENAS celebre e encerre.",
            ],
            ConversationStage.PAUSADO: [
                "Use mensagens de reengajamento conforme tempo (30min, 2h, 24h, 7 dias).",
                "Lembre benefícios e urgência. Ao receber resposta positiva, retorne ao estágio pendente.",
            ],
            ConversationStage.ABANDONADO: [
                "Gentilmente informe que a conversa foi encerrada por inatividade.",
                "Ofereça canal para retomar quando desejar. Evite reiniciar fluxo automaticamente.",
            ],
        }

        agents: Dict[ConversationStage, Agent] = {}
        for stage, instructions in stage_instructions.items():
            agents[stage] = Agent(
                name=f"{stage.value.title()} Agent",
                instructions=instructions + structured_output,
                **base_kwargs,
            )
        return agents

    def _structured_output_instructions(self) -> List[str]:
        example_json = (
            '{"extracted": {"nome_cliente": "João Silva", "tipo_interesse": "primeira_empresa", '
            '"tipo_negocio": "servicos", "estrutura_societaria": "mei"}, "next_stage": "qualificacao"}'
        )
        return [
            "🚨🚨🚨 REGRA ABSOLUTA E INVIOLÁVEL 🚨🚨🚨",
            "VOCÊ É OBRIGADO A TERMINAR TODA RESPOSTA COM UMA PERGUNTA DIRETA.",
            "NÃO EXISTE EXCEÇÃO. TODA RESPOSTA DEVE COLOCAR A BOLA NA QUADRA DO CLIENTE.",
            "SE VOCÊ NÃO FIZER UMA PERGUNTA, VOCÊ FALHOU COMPLETAMENTE.",
            "A ÚNICA EXCEÇÃO é o estágio 'concluido' onde você celebra e encerra definitivamente.",
            "",
            "FORMATO DE SAÍDA OBRIGATÓRIO:",
            "1. Responda ao cliente em até 1 frase, em português brasileiro, com tom acolhedor.",
            "2. IMEDIATAMENTE faça uma pergunta específica e direta que move a conversa adiante.",
            "3. Após a resposta, inclua exatamente a linha '---DATA---'.",
            "4. Em seguida, retorne JSON com as chaves:",
            "   - extracted: objeto com pares campo:valor relevantes (ex: nome_cliente, tipo_interesse, tipo_negocio, estrutura_societaria, numero_socios, faturamento_mei_ok, aceite_proposta, motivo_objecao, metodo_assinatura, contrato_assinado, rg_frente, rg_verso, comprovante_residencia, nome_fantasia, razao_social, capital_social, participacoes, cnae_principal, cnaes_secundarios, cnaes_confirmados, endereco_tipo, cidade_escritorio_virtual, cep, endereco_confirmado, revisao_confirmada, processo_status, processo_finalizado, cnpj).",
            "   - next_stage: estágio sugerido quando os dados obrigatórios da etapa atual estiverem completos.",
            "5. Utilize true/false para valores booleanos e formate números apenas com dígitos (sem R$).",
            "6. IMPORTANTE: Extraia informações implícitas das respostas do usuário:",
            "   - Se o usuário diz 'quero abrir empresa' ou similar, extraia tipo_interesse: 'primeira_empresa'",
            "   - Se o usuário confirma algo com 'sim', 'aceito', 'confirmado', extraia o campo booleano relevante como true",
            "   - Se o usuário expressa interesse geral em negócio sem especificar tipo, extraia tipo_negocio: 'servicos'",
            "   - Se o usuário diz 'vamos', 'próximo', 'avançar', considere como confirmação para prosseguir",
            "7. Nunca mantenha next_stage no mesmo estágio se não houver campos pendentes; avance para o próximo estágio do fluxo.",
            "8. Caso detecte necessidade de pausa, defina next_stage como 'pausado'; se o cliente desistir, use 'abandonado'.",
            "",
            "EXEMPLOS OBRIGATÓRIOS DE COMO SEMPRE TERMINAR COM PERGUNTA:",
            "❌ ERRADO: 'Que excelente iniciativa! Abrir uma nova empresa é um passo muito importante.'",
            "✅ CORRETO: 'Que ótimo! Como posso te chamar?'",
            "❌ ERRADO: 'É um prazer, Rafael! Com seu nome e interesse, já temos informações importantes.'",
            "✅ CORRETO: 'Prazer, Rafael! Você está pensando em abrir sua primeira empresa?'",
            "❌ ERRADO: 'Perfeito! Estou aqui para te ajudar.'",
            "✅ CORRETO: 'Perfeito! Seu negócio será de comércio, serviços ou indústria?'",
            "",
            f"Exemplo JSON: {example_json}",
        ]

    # ------------------------------------------------------------------
    # Router step construction
    # ------------------------------------------------------------------
    def _build_stage_steps(self) -> Dict[ConversationStage, Steps]:
        steps: Dict[ConversationStage, Steps] = {}
        for stage, agent in self._agents.items():
            steps[stage] = Steps(
                name=f"{stage.value}_pipeline",
                steps=[
                    Step(
                        name=f"{stage.value}_agent",
                        executor=self._make_stage_executor(stage, agent),
                    ),
                    Step(
                        name=f"{stage.value}_postprocess",
                        executor=self._make_postprocess_executor(stage),
                    ),
                ],
            )
        return steps

    def _make_stage_executor(self, stage: ConversationStage, agent: Agent):
        def _executor(step_input: StepInput) -> StepOutput:
            context = self._ensure_context()
            user_input = self._latest_user_input or (step_input.message or "")
            prompt = self._build_stage_prompt(stage, context, str(user_input))
            try:
                response = agent.run(prompt, session_id=self.session_id, stream=False)
                content = response.content or ""
            except Exception as exc:  # pragma: no cover - LLM/runtime guard
                logger.exception("Agent %s failed on stage %s: %s", agent.name, stage.value, exc)
                content = (
                    "Desculpe, enfrentei uma instabilidade. Pode repetir ou tentar novamente em instantes?"
                )
                response = RunResponse(content=content)

            return StepOutput(
                step_name=f"{stage.value}_agent",
                executor_type="agent",
                executor_name=agent.name,
                content=content,
                response=response,
            )

        return _executor

    def _make_postprocess_executor(self, stage: ConversationStage):
        def _executor(step_input: StepInput) -> StepOutput:
            return self._postprocess_agent_output(step_input, stage)

        return _executor

    # ------------------------------------------------------------------
    # Prompt building helpers
    # ------------------------------------------------------------------
    def _build_stage_prompt(
        self,
        stage: ConversationStage,
        context: ConversationContext,
        user_input: str,
    ) -> str:
        history = self._get_recent_history(context)
        summary = self._render_context_summary(context)
        missing = ", ".join(self._get_missing_fields(stage, context)) or "nenhum campo pendente"
        objective = self._stage_objective(stage)

        # Add specific instruction for pushing conversation forward
        if stage == ConversationStage.CONCLUIDO:
            conversation_rule = (
                "🚨 REGRA ESPECIAL PARA ESTÁGIO CONCLUÍDO 🚨\n"
                "Este é o ÚNICO estágio onde você NÃO faz perguntas.\n"
                "Celebre, informe que está concluído, e ENCERRE definitivamente.\n"
                "TERMINE com: 'Este atendimento está CONCLUÍDO.'"
            )
        else:
            conversation_rule = (
                "🚨🚨🚨 REGRA ABSOLUTA E INVIOLÁVEL 🚨🚨🚨\n"
                "VOCÊ É OBRIGADO A TERMINAR SUA RESPOSTA COM UMA PERGUNTA DIRETA.\n"
                "NÃO EXISTE EXCEÇÃO. NÃO EXISTE DESCULPA.\n"
                "SE VOCÊ NÃO FIZER UMA PERGUNTA, VOCÊ FALHOU COMPLETAMENTE.\n"
                "NUNCA diga apenas 'Que ótimo!' ou 'Perfeito!' sem uma pergunta.\n"
                "SEMPRE termine com: 'Como posso te chamar?' ou 'Seu negócio será de que tipo?' ou similar.\n"
                "A conversa PARA se você não fizer uma pergunta."
            )

        return (
            f"{conversation_rule}\n\n"
            "Resumo das últimas mensagens:\n"
            f"{history}\n\n"
            "Visão geral dos dados coletados até agora:\n"
            f"{summary}\n\n"
            f"Campos pendentes para este estágio: {missing}\n"
            f"Estágio atual: {stage.value}\n"
            f"Mensagem do cliente: \"{user_input}\"\n\n"
            f"Objetivo imediato: {objective}\n"
            "AVANÇO OBRIGATÓRIO: conduza o cliente ao próximo passo, mantendo tom acolhedor e celebrando cada progresso."
            " Respeite as instruções do estágio atual e atualize o JSON de dados conforme necessário."
        )

    @staticmethod
    def _get_recent_history(context: ConversationContext, limit: int = 6) -> str:
        entries = context.messages_exchanged[-limit:]
        if not entries:
            return "(sem histórico relevante)"
        rendered = []
        for item in entries:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            rendered.append(f"{role}: {content}")
        return "\n".join(rendered)

    def _render_context_summary(self, context: ConversationContext) -> str:
        lead = context.lead_data
        business = context.business_profile
        proposal = context.proposal_status
        contract = context.contract_data
        documents = context.document_status
        company = context.company_profile
        review = context.review_status
        process = context.process_status

        sections = [
            "👤 Cliente",
            f"- Nome: {lead.nome_completo or '[pendente]'}",
            f"- Interesse: {lead.tipo_interesse or '[pendente]'}",
            f"- Email: {lead.email or '[pendente]'} | Telefone: {lead.telefone or '[pendente]'}",
            "\n💡 Perfil do Negócio",
            f"- Tipo de negócio: {business.get('tipo_negocio', '[pendente]')}",
            f"- Estrutura societária: {business.get('estrutura_societaria', '[pendente]')}",
            f"- Nº de sócios: {business.get('numero_socios', 'N/A')}",
            "\n💼 Proposta",
            f"- Aceite: {proposal.get('aceite_proposta', '[pendente]')}",
            f"- Objeção: {proposal.get('motivo_objecao', 'nenhuma')}",
            "\n📝 Contrato",
            f"- Dados conferidos: {contract.get('nome_completo') or '[pendente]'}",
            f"- CPF: {contract.get('cpf') or '[pendente]'}",
            f"- Assinado: {contract.get('contrato_assinado', False)}",
            "\n📎 Documentos",
            f"- RG/CNH frente: {bool(documents.get('rg_frente'))}",
            f"- RG/CNH verso: {bool(documents.get('rg_verso'))}",
            f"- Comprovante: {bool(documents.get('comprovante_residencia'))}",
            "\n🏢 Empresa",
            f"- Nome fantasia: {company.get('nome_fantasia', '[pendente]')}",
            f"- Capital social: {company.get('capital_social', '[pendente]')}",
            f"- CNAE principal: {company.get('cnae_principal', '[pendente]')}",
            f"- Endereço: {company.get('endereco_completo', '[pendente]')}",
            "\n✅ Revisão",
            f"- Revisão confirmada: {review.get('confirmado', False)}",
            "\n🚀 Processo",
            f"- Status: {process.get('status', '[aguardando]')} | CNPJ: {process.get('cnpj', '---')}",
        ]
        return "\n".join(sections)

    def _get_missing_fields(self, stage: ConversationStage, context: ConversationContext) -> List[str]:
        lead = context.lead_data
        business = context.business_profile
        proposal = context.proposal_status
        contract = context.contract_data
        documents = context.document_status
        company = context.company_profile
        review = context.review_status
        process = context.process_status

        missing: List[str] = []

        if stage == ConversationStage.INICIAL:
            if not lead.nome_completo:
                missing.append("nome do cliente")
            if not lead.tipo_interesse:
                missing.append("tipo de interesse")
        elif stage == ConversationStage.QUALIFICACAO:
            if not business.get("tipo_negocio"):
                missing.append("tipo de negócio")
            if not business.get("estrutura_societaria"):
                missing.append("estrutura societária")
            estrutura = business.get("estrutura_societaria")
            if estrutura == "mei" and business.get("faturamento_mei_ok") is None:
                missing.append("confirmação de faturamento MEI")
            if estrutura == "socios" and not business.get("numero_socios"):
                missing.append("número de sócios")
        elif stage == ConversationStage.PROPOSTA:
            aceite = proposal.get("aceite_proposta")
            if aceite is not True:
                missing.append("aceite da proposta")
        elif stage == ConversationStage.CONTRATACAO:
            # Check if we have the required contract data
            # Data can be in contract_data section or lead_data section
            nome_completo = contract.get("nome_completo") or lead.nome_completo
            cpf = contract.get("cpf") or lead.cpf
            email = contract.get("email") or lead.email
            telefone = contract.get("telefone") or lead.telefone
            data_nascimento = contract.get("data_nascimento") or lead.data_nascimento

            if not nome_completo:
                missing.append("nome completo para contrato")
            if not cpf:
                missing.append("CPF")
            if not email:
                missing.append("email para contrato")
            if not telefone:
                missing.append("telefone para contrato")
            if not data_nascimento:
                missing.append("data de nascimento")
            if not contract.get("metodo_assinatura"):
                missing.append("método de assinatura")
            if contract.get("contrato_assinado") is not True:
                missing.append("confirmação de assinatura")
        elif stage == ConversationStage.COLETA_DOCUMENTOS_PESSOAIS:
            if not documents.get("rg_frente"):
                missing.append("foto frente RG/CNH")
            if not documents.get("rg_verso"):
                missing.append("foto verso RG/CNH")
            if not documents.get("comprovante_residencia"):
                missing.append("comprovante de residência")
        elif stage == ConversationStage.DEFINICAO_EMPRESA:
            if not company.get("nome_fantasia"):
                missing.append("nome fantasia")
            if not company.get("razao_social"):
                missing.append("razão social")
            if company.get("capital_social") is None:
                missing.append("capital social")
            numero_socios = business.get("numero_socios") or 0
            if numero_socios and not company.get("participacoes_definidas"):
                missing.append("divisão das participações")
        elif stage == ConversationStage.ESCOLHA_CNAE:
            if not company.get("cnae_principal"):
                missing.append("CNAE principal")
            if company.get("cnaes_confirmados") is not True:
                missing.append("confirmação de CNAEs")
        elif stage == ConversationStage.ENDERECO_COMERCIAL:
            endereco_tipo = company.get("endereco_tipo")
            if not endereco_tipo:
                missing.append("escolha do tipo de endereço")
            elif endereco_tipo == "virtual":
                if not company.get("cidade_escritorio_virtual"):
                    missing.append("cidade do escritório virtual")
                if company.get("aceite_escritorio_virtual") is not True:
                    missing.append("aceite do escritório virtual")
            else:
                if not company.get("cep"):
                    missing.append("CEP")
                if not company.get("numero"):
                    missing.append("número do endereço")
                if company.get("endereco_confirmado") is not True:
                    missing.append("confirmação do endereço")
        elif stage == ConversationStage.REVISAO_FINAL:
            if review.get("confirmado") is not True:
                missing.append("confirmação final")
        elif stage == ConversationStage.PROCESSAMENTO:
            if process.get("finalizado") is not True:
                missing.append("finalização do processamento")
        return missing

    def _stage_objective(self, stage: ConversationStage) -> str:
        mapping = {
            ConversationStage.INICIAL: "acolher o cliente, coletar nome e entender o interesse",
            ConversationStage.QUALIFICACAO: "mapear necessidades e confirmar elegibilidade",
            ConversationStage.PROPOSTA: "apresentar proposta personalizada e obter aceite",
            ConversationStage.CONTRATACAO: "formalizar dados contratuais e coletar assinatura",
            ConversationStage.COLETA_DOCUMENTOS_PESSOAIS: "receber documentos pessoais com qualidade",
            ConversationStage.DEFINICAO_EMPRESA: "definir identidade corporativa (nome, capital, participação)",
            ConversationStage.ESCOLHA_CNAE: "selecionar CNAE principal e atividades secundárias",
            ConversationStage.ENDERECO_COMERCIAL: "definir endereço comercial mais vantajoso",
            ConversationStage.REVISAO_FINAL: "validar todos os dados antes da abertura",
            ConversationStage.PROCESSAMENTO: "acompanhar etapas internas e informar progresso",
            ConversationStage.CONCLUIDO: "celebrar abertura e orientar primeiros passos",
            ConversationStage.PAUSADO: "reengajar cliente com mensagens personalizadas",
            ConversationStage.ABANDONADO: "encerrar cordialmente e oferecer retorno futuro",
        }
        return mapping.get(stage, "manter a conversa em andamento")

    # ------------------------------------------------------------------
    # Stage routing and transitions
    # ------------------------------------------------------------------
    def _route_conversation_state(self, step_input: StepInput) -> List[Steps]:
        context = self._ensure_context()
        user_input = step_input.message or self._latest_user_input
        text = str(user_input).lower()

        if self._detect_completion_request(text) and context.stage not in {
            ConversationStage.PROCESSAMENTO,
            ConversationStage.CONCLUIDO,
        }:
            context.stage = ConversationStage.PAUSADO
            self._store_context_in_state()
            return [self._stage_steps[ConversationStage.PAUSADO]]

        computed_stage = self._determine_primary_stage(context)
        context.stage = computed_stage
        self._store_context_in_state()

        return [
            self._stage_steps.get(
                computed_stage,
                self._stage_steps[ConversationStage.INICIAL],
            )
        ]

    def _determine_primary_stage(self, context: ConversationContext) -> ConversationStage:
        # Keep special states if already set
        if context.stage in {ConversationStage.PAUSADO, ConversationStage.ABANDONADO, ConversationStage.CONCLUIDO}:
            logger.debug(f"Keeping special stage: {context.stage}")
            return context.stage

        process_status = context.process_status
        if process_status.get("status") == "abandonado":
            logger.debug("Process status indicates abandoned")
            return ConversationStage.ABANDONADO

        for stage in PRIMARY_STAGE_SEQUENCE:
            if stage == ConversationStage.CONCLUIDO:
                process_finalizado = context.process_status.get("finalizado")
                if process_finalizado:
                    logger.debug("Process finalized, moving to CONCLUIDO")
                    return ConversationStage.CONCLUIDO
                # otherwise remain in PROCESSAMENTO until finalizado
                continue

            missing = self._get_missing_fields(stage, context)
            if missing:
                logger.debug(f"Stage {stage.value} has missing fields: {missing}")
                return stage
            else:
                logger.debug(f"Stage {stage.value} is complete, checking next stage")

        if context.process_status.get("finalizado"):
            logger.debug("All stages complete and process finalized")
            return ConversationStage.CONCLUIDO
        logger.debug("All stages complete, moving to PROCESSAMENTO")
        return ConversationStage.PROCESSAMENTO

    def _apply_stage_transition(
        self,
        context: ConversationContext,
        previous_stage: ConversationStage,
        suggested_stage: Optional[ConversationStage],
    ) -> None:
        computed_stage = self._determine_primary_stage(context)

        logger.debug(f"Stage transition: {previous_stage.value} -> suggested: {suggested_stage} -> computed: {computed_stage.value}")

        if suggested_stage in {ConversationStage.PAUSADO, ConversationStage.ABANDONADO}:
            logger.debug(f"Applying special stage transition to {suggested_stage}")
            context.stage = suggested_stage
            return

        if suggested_stage and suggested_stage in PRIMARY_STAGE_SEQUENCE:
            try:
                suggested_index = PRIMARY_STAGE_SEQUENCE.index(suggested_stage)
                computed_index = PRIMARY_STAGE_SEQUENCE.index(computed_stage)
                if suggested_index >= computed_index:
                    logger.debug(f"Accepting suggested stage {suggested_stage.value} (index {suggested_index} >= {computed_index})")
                    context.stage = suggested_stage
                    return
                else:
                    logger.debug(f"Rejecting suggested stage {suggested_stage.value} (index {suggested_index} < {computed_index})")
            except ValueError:
                logger.warning("Invalid stage suggestion: %s", suggested_stage)

        logger.debug(f"Using computed stage: {computed_stage.value}")
        context.stage = computed_stage

    # ------------------------------------------------------------------
    # Context updates & persistence
    # ------------------------------------------------------------------
    def _postprocess_agent_output(self, step_input: StepInput, stage: ConversationStage) -> StepOutput:
        agent_output = self._extract_agent_output(step_input)
        raw_response = agent_output.content if agent_output else ""
        message, extracted, suggested_stage = self._parse_agent_response(raw_response)

        context = self._ensure_context()
        if message:
            context.messages_exchanged.append(
                {
                    "role": "assistant",
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        self._update_context_with_extracted_data(context, extracted)
        self._apply_stage_transition(context, stage, suggested_stage)
        context.conversation_turns += 1
        context.last_interaction_at = datetime.now()
        self._trim_history(context)
        self._persist_context(context)

        return StepOutput(
            step_name=f"{stage.value}_postprocess",
            executor_type="function",
            executor_name="postprocess_agent_output",
            content=message or raw_response,
        )

    @staticmethod
    def _extract_agent_output(step_input: StepInput) -> Optional[StepOutput]:
        previous = step_input.previous_step_outputs or {}
        if not previous:
            return None
        last_key = list(previous.keys())[-1]
        return previous[last_key]

    def _parse_agent_response(
        self, raw_response: Optional[str]
    ) -> Tuple[str, Dict[str, Any], Optional[ConversationStage]]:
        if not raw_response:
            return "", {}, None

        message_text = raw_response.strip()
        extracted: Dict[str, Any] = {}
        suggested_stage: Optional[ConversationStage] = None

        if "---DATA---" in raw_response:
            message_part, data_part = raw_response.split("---DATA---", 1)
            message_text = message_part.strip()
            json_text = data_part.strip().replace("```json", "").replace("```", "").strip()
            if json_text:
                try:
                    payload = json.loads(json_text)
                    if isinstance(payload, dict):
                        extracted = payload.get("extracted", {}) or {}
                        next_stage_value = payload.get("next_stage") or payload.get("stage")
                        if next_stage_value:
                            try:
                                suggested_stage = ConversationStage(next_stage_value)
                            except ValueError:
                                logger.warning("Invalid next_stage from agent: %s", next_stage_value)
                    else:
                        logger.warning("Structured payload is not a dict: %s", json_text)
                except json.JSONDecodeError:
                    logger.error("Failed to parse structured agent response: %s", json_text)

        return message_text, extracted, suggested_stage

    def _update_context_with_extracted_data(
        self, context: ConversationContext, extracted: Dict[str, Any]
    ) -> None:
        if not extracted:
            return

        for field, value in extracted.items():
            section_field = FIELD_SECTION_MAP.get(field)
            if not section_field:
                continue
            section, attribute = section_field
            parsed_value = self._coerce_value(attribute, value)
            if parsed_value is None and value not in (None, ""):
                parsed_value = value

            if section == "lead_data":
                current_value = getattr(context.lead_data, attribute, None)
                if parsed_value and current_value != parsed_value:
                    setattr(context.lead_data, attribute, parsed_value)
                    self._track_field_collection(context, attribute)
            else:
                section_dict = getattr(context, section)
                current_value = section_dict.get(attribute)
                if parsed_value not in (None, "") and current_value != parsed_value:
                    section_dict[attribute] = parsed_value
                    self._track_field_collection(context, f"{section}.{attribute}")

        # keep qualification flag updated
        context.check_qualification()

        # Sync contract data between sections for consistency
        self._sync_contract_data(context)

        # Infer missing structured choices from latest messages when LLM did not emit them
        self._apply_fallback_inferences(context)

    def _coerce_value(self, key: str, value: Any) -> Any:
        if value is None:
            return None
        if key in BOOL_KEYS:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"sim", "yes", "y", "true", "verdade", "confirmo", "ok"}:
                    return True
                if lowered in {"não", "nao", "no", "false", "n"}:
                    return False
            return None
        if key in INT_KEYS:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        if key in FLOAT_KEYS:
            try:
                cleaned = str(value).replace("R$", "").replace(".", "").replace(",", ".")
                return float(cleaned)
            except (TypeError, ValueError):
                return None
        if key in LIST_KEYS:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                parts = [p.strip() for p in re.split(r"[,;]", value) if p.strip()]
                return parts
        if key == "cpf":
            digits = re.sub(r"\D", "", str(value))
            if len(digits) == 11:
                return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            return None
        if key == "tipo_interesse":
            normalized = re.sub(r"[^a-z0-9 ]", "", str(value).lower()).strip()
            mapping = {
                "1": "primeira_empresa",
                "primeira": "primeira_empresa",
                "primeira empresa": "primeira_empresa",
                "abrindo primeira empresa": "primeira_empresa",
                "primeira_empresa": "primeira_empresa",
                "2": "nova_empresa",
                "nova": "nova_empresa",
                "nova empresa": "nova_empresa",
                "abrindo nova empresa": "nova_empresa",
                "tenho outras": "nova_empresa",
                "tenho outra": "nova_empresa",
                "nova_empresa": "nova_empresa",
                "3": "conhecendo",
                "conhecendo": "conhecendo",
                "apenas conhecendo": "conhecendo",
                "somente conhecendo": "conhecendo",
                "curioso": "conhecendo",
            }
            return mapping.get(normalized)
        if key == "tipo_negocio":
            normalized = re.sub(r"[^a-z ]", "", str(value).lower()).strip()
            mapping = {
                "comercio": "comercio",
                "comércio": "comercio",
                "venda": "comercio",
                "produtos": "comercio",
                "servicos": "servicos",
                "serviços": "servicos",
                "servico": "servicos",
                "serviço": "servicos",
                "consultoria": "servicos",
                "industria": "industria",
                "indústria": "industria",
                "industrial": "industria",
                "fabricacao": "industria",
                "fabricação": "industria",
                "misto": "misto",
                "comercio servicos": "misto",
                "comércio serviços": "misto",
                "comercio e servicos": "misto",
                "comércio e serviços": "misto",
            }
            return mapping.get(normalized, normalized or None)
        if key == "estrutura_societaria":
            normalized = re.sub(r"[^a-z ]", "", str(value).lower()).strip()
            mapping = {
                "mei": "mei",
                "sozinho": "mei",
                "individual": "mei",
                "sem socios": "mei",
                "sem sócios": "mei",
                "socios": "socios",
                "sócios": "socios",
                "com socios": "socios",
                "com sócios": "socios",
                "sociedade": "socios",
                "ltda": "socios",
                "indefinido": "indefinido",
                "ainda nao sei": "indefinido",
                "ainda não sei": "indefinido",
                "nao sei": "indefinido",
                "não sei": "indefinido",
            }
            return mapping.get(normalized, normalized or None)
        if key == "metodo_assinatura":
            normalized = re.sub(r"[^a-z ]", "", str(value).lower()).strip()
            mapping = {
                "sms": "sms",
                "celular": "sms",
                "telefone": "sms",
                "mensagem": "sms",
                "email": "email",
                "e mail": "email",
                "e-mail": "email",
                "whatsapp": "whatsapp",
                "zap": "whatsapp",
            }
            return mapping.get(normalized, normalized or None)
        if key == "endereco_tipo":
            normalized = re.sub(r"[^a-z ]", "", str(value).lower()).strip()
            mapping = {
                "virtual": "virtual",
                "escritorio virtual": "virtual",
                "escritório virtual": "virtual",
                "residencial": "residencial",
                "casa": "residencial",
                "comercial": "comercial",
                "escritorio proprio": "comercial",
                "escritório proprio": "comercial",
                "escritorio próprio": "comercial",
                "escritório próprio": "comercial",
            }
            return mapping.get(normalized, normalized or None)
        if isinstance(value, str):
            return value.strip()
        return value

    @staticmethod
    def _track_field_collection(context: ConversationContext, field_name: str) -> None:
        if field_name not in context.fields_collected:
            context.fields_collected.append(field_name)

    @staticmethod
    def _sync_contract_data(context: ConversationContext) -> None:
        """Sync contract data between lead_data and contract_data sections for consistency."""
        lead = context.lead_data
        contract = context.contract_data

        # If we have contract-specific data, ensure it's also in lead_data
        if contract.get("nome_completo") and not lead.nome_completo:
            lead.nome_completo = contract["nome_completo"]
        if contract.get("cpf") and not lead.cpf:
            lead.cpf = contract["cpf"]
        if contract.get("email") and not lead.email:
            lead.email = contract["email"]
        if contract.get("telefone") and not lead.telefone:
            lead.telefone = contract["telefone"]
        if contract.get("data_nascimento") and not lead.data_nascimento:
            lead.data_nascimento = contract["data_nascimento"]

        # If we have lead data but missing contract data, sync it
        if lead.nome_completo and not contract.get("nome_completo"):
            contract["nome_completo"] = lead.nome_completo
        if lead.cpf and not contract.get("cpf"):
            contract["cpf"] = lead.cpf
        if lead.email and not contract.get("email"):
            contract["email"] = lead.email
        if lead.telefone and not contract.get("telefone"):
            contract["telefone"] = lead.telefone
        if lead.data_nascimento and not contract.get("data_nascimento"):
            contract["data_nascimento"] = lead.data_nascimento

    def _apply_fallback_inferences(self, context: ConversationContext) -> None:
        latest_user_message = next(
            (m["content"].lower() for m in reversed(context.messages_exchanged) if m.get("role") == "user"),
            "",
        )

        # Infer tipo_interesse if still missing
        if not context.lead_data.tipo_interesse and latest_user_message:
            context.lead_data.tipo_interesse = self._infer_tipo_interesse(latest_user_message)
            if context.lead_data.tipo_interesse:
                self._track_field_collection(context, "tipo_interesse")

        # Infer estrutura societária if not set yet
        if not context.business_profile.get("estrutura_societaria") and latest_user_message:
            inferred = self._infer_estrutura_societaria(latest_user_message)
            if inferred:
                context.business_profile["estrutura_societaria"] = inferred
                self._track_field_collection(context, "business_profile.estrutura_societaria")

        # Infer tipo_negocio if not set yet
        if not context.business_profile.get("tipo_negocio") and latest_user_message:
            inferred = self._infer_tipo_negocio(latest_user_message)
            if inferred:
                context.business_profile["tipo_negocio"] = inferred
                self._track_field_collection(context, "business_profile.tipo_negocio")

    @staticmethod
    def _infer_tipo_interesse(user_text: str) -> Optional[str]:
        cleaned = re.sub(r"[^a-z0-9 ]", "", user_text.lower()).strip()
        if any(token in cleaned for token in ["1", "primeira"]):
            return "primeira_empresa"
        if any(token in cleaned for token in ["2", "nova", "outra", "outras"]):
            return "nova_empresa"
        if any(token in cleaned for token in ["3", "conhecendo", "curios", "avaliando"]):
            return "conhecendo"
        return None

    @staticmethod
    def _infer_estrutura_societaria(user_text: str) -> Optional[str]:
        cleaned = re.sub(r"[^a-z ]", "", user_text.lower()).strip()
        if any(token in cleaned for token in ["sozinho", "mei", "individual"]):
            return "mei"
        if "socio" in cleaned or "sócio" in cleaned or "socios" in cleaned:
            return "socios"
        if "nao sei" in cleaned or "não sei" in cleaned or "duvida" in cleaned:
            return "indefinido"
        return None

    @staticmethod
    def _infer_tipo_negocio(user_text: str) -> Optional[str]:
        """Infer business type from user message when they express general business intent."""
        cleaned = re.sub(r"[^a-z ]", "", user_text.lower()).strip()

        # If user expresses general business intent without specifying type,
        # default to "servicos" as it's the most common for new entrepreneurs
        business_intent_keywords = [
            "abrir empresa", "primeira empresa", "nova empresa", "meu negocio",
            "minha empresa", "empreender", "negocio proprio", "trabalhar por conta"
        ]

        if any(keyword in cleaned for keyword in business_intent_keywords):
            # Check for specific business type indicators first
            if any(word in cleaned for word in ["vender", "produto", "loja", "comercio"]):
                return "comercio"
            elif any(word in cleaned for word in ["fabrica", "producao", "industria", "manufatura"]):
                return "industria"
            elif any(word in cleaned for word in ["servico", "consultoria", "atendimento", "prestacao"]):
                return "servicos"
            else:
                # Default to services for general business intent
                return "servicos"

        return None

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _detect_completion_request(self, text: str) -> bool:
        keywords = [
            "stop",
            "pausar",
            "pausa",
            "depois",
            "mais tarde",
            "não agora",
            "nao agora",
            "volto",
            "encerrar",
            "finalizar",
        ]
        return any(keyword in text for keyword in keywords)

    def _trim_history(self, context: ConversationContext, limit: int = 50) -> None:
        if len(context.messages_exchanged) > limit:
            context.messages_exchanged = context.messages_exchanged[-limit:]

    # ------------------------------------------------------------------
    # Session state & persistence helpers (unchanged core logic)
    # ------------------------------------------------------------------
    @property
    def session_state(self) -> Dict[str, Any]:
        if self.workflow_session_state is None:
            self.workflow_session_state = {}
        if "context" not in self.workflow_session_state:
            self._hydrate_context_from_storage()
        return self.workflow_session_state

    @session_state.setter
    def session_state(self, value: Dict[str, Any]) -> None:
        self.workflow_session_state = value

    def _ensure_context(self) -> ConversationContext:
        if self._context is None:
            self._hydrate_context_from_storage()
        return self._context

    def _hydrate_context_from_storage(self) -> None:
        """Load context from database storage or create new one."""
        context_data = None

        # Try to load from current session state first
        if self.workflow_session_state and "context" in self.workflow_session_state:
            context_data = self.workflow_session_state.get("context")
        else:
            # Load session state from database
            self._load_session_state_from_db()
            if self.workflow_session_state and "context" in self.workflow_session_state:
                context_data = self.workflow_session_state.get("context")

        if context_data:
            try:
                self._context = ConversationContext(**context_data)
            except Exception as exc:  # pragma: no cover - resilience
                logger.warning("Failed to hydrate context from storage: %s", exc)
                self._context = ConversationContext()
        else:
            self._context = ConversationContext()

        self._store_context_in_state()

    def _store_context_in_state(self) -> None:
        if self._context is None:
            self._context = ConversationContext()
        if self.workflow_session_state is None:
            self.workflow_session_state = {}
        self.workflow_session_state["context"] = self._serialize_context(self._context)

    def _persist_context(self, context: ConversationContext) -> None:
        """Persist context to database storage."""
        self._context = context

        # Store in Agno's session state for current execution
        self.session_state["context"] = self._serialize_context(context)
        self._store_context_in_state()

        # Manually persist session state to database since Agno doesn't do this automatically
        self._save_session_state_to_db()

    def _ensure_session_loaded(self) -> None:
        if self.workflow_session is None:
            self.load_session()

    def _save_session_state_to_db(self) -> None:
        """Manually save session state to database using workflow session."""
        try:
            if not self.session_state:
                return

            # Ensure we have a workflow session
            self._ensure_session_loaded()

            if self.workflow_session and self.storage:
                # Set the session data
                session_data_to_save = dict(self.session_state)
                self.workflow_session.session_data = session_data_to_save

                # Use the storage's upsert method with the workflow session
                # This bypasses the broken write_to_storage() method
                self.storage.upsert(self.workflow_session)

        except Exception as exc:
            logger.warning("Failed to save session state to database: %s", exc)

    def _load_session_state_from_db(self) -> None:
        """Manually load session state from database using workflow session."""
        try:
            if not self.storage or not self.session_id:
                if self.workflow_session_state is None:
                    self.workflow_session_state = {}
                return

            # Use storage to load the session
            session_record = self.storage.read(self.session_id)

            if session_record and hasattr(session_record, 'session_data') and session_record.session_data:
                # Restore session state from database
                self.workflow_session_state = dict(session_record.session_data)
            else:
                if self.workflow_session_state is None:
                    self.workflow_session_state = {}

        except Exception as exc:
            logger.warning("Failed to load session state from database: %s", exc)
            if self.workflow_session_state is None:
                self.workflow_session_state = {}

    def _serialize_context(self, context: ConversationContext) -> Dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {key: convert(val) for key, val in value.items()}
            if hasattr(value, "model_dump"):
                return convert(value.model_dump())
            return value

        return convert(context.model_dump())

    def _save_session_state(self) -> None:
        """Save the current context state to storage."""
        if self._context is not None:
            self._persist_context(self._context)

    def _get_context(self) -> ConversationContext:
        return self._ensure_context()

    def reset(self) -> None:
        self.session_state.clear()
        self._context = ConversationContext()
        self._persist_context(self._context)

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------
    def run(self, user_input: str = "", **kwargs) -> Iterator[RunResponse]:
        message = user_input or ""
        self._latest_user_input = message
        context = self._ensure_context()
        computed_stage = self._determine_primary_stage(context)
        if context.stage != computed_stage:
            context.stage = computed_stage
            self._store_context_in_state()
        self._record_user_message(message)

        try:
            workflow_response = super().run(
                message=message,
                session_id=self.session_id,
                user_id=self.user_id,
                stream=False,
                **kwargs,
            )
            final_message = self._safe_extract_content(workflow_response)
            if final_message:
                yield RunResponse(content=final_message)
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("State machine execution failed: %s", exc)
            fallback = (
                "Desculpe, tivemos um imprevisto técnico. Nossa equipe já está cuidando disso. Pode tentar novamente em instantes?"
            )
            yield RunResponse(content=fallback)
        finally:
            if self._context is not None:
                self._save_session_state()
            self._latest_user_input = ""

    def _record_user_message(self, user_input: str) -> None:
        context = self._ensure_context()
        if user_input:
            context.messages_exchanged.append(
                {
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            context.last_interaction_at = datetime.now()
            self._trim_history(context)
            self._persist_context(context)  # Changed from _store_context_in_state() to _persist_context()

    @staticmethod
    def _safe_extract_content(workflow_response: WorkflowRunResponse) -> str:
        if workflow_response is None:
            return ""
        content = workflow_response.content
        if isinstance(content, str):
            return content
        if content is None:
            return ""
        try:
            return json.dumps(content, ensure_ascii=False)
        except TypeError:
            return str(content)


LeadConversionStateMachine = LeadConversionWorkflow


def get_lead_conversion_workflow(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> LeadConversionWorkflow:
    """Factory maintained for backwards compatibility."""

    return LeadConversionWorkflow(session_id=session_id, user_id=user_id)
