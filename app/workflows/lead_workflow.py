"""
Lead Conversion Workflow (Agno v2)

Router-based implementation for the Brazilian accounting lead
conversion chatbot. Provides multi-agent routing, persistent
conversation context and compatibility with existing v1 helpers.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agno.agent import Agent, RunResponse
from agno.models.openrouter import OpenRouter
from agno.run.v2.workflow import WorkflowRunResponse
from agno.workflow.v2.router import Router
from agno.workflow.v2.step import Step
from agno.workflow.v2.steps import Steps
from agno.workflow.v2.types import StepInput, StepOutput
from agno.workflow.v2.workflow import Workflow as WorkflowV2

from app.core.database import get_agent_storage, get_workflow_storage
from app.models.lead_models import ConversationContext, ConversationStage

logger = logging.getLogger(__name__)


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
            name="Lead Conversion State Machine",
            description="Workflow multiagente com roteamento por estágio",
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

        agents = {
            ConversationStage.GREETING: Agent(
                name="Greeting Agent",
                instructions=[
                    "Você é o agente de boas-vindas da Agilize Contabilidade.",
                    "Objetivo: criar rapport inicial e obter o nome completo do cliente.",
                    "Use tom caloroso, profissional e respostas curtas (até 2 frases).",
                    "Assim que o nome completo for identificado, defina next_stage como 'data_collection' e direcione para coleta de contatos.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.DATA_COLLECTION: Agent(
                name="Data Collection Agent",
                instructions=[
                    "Você coleta dados de contato essenciais (email e telefone).",
                    "Avance sempre perguntando um dado por vez e validando formato.",
                    "Reforce benefícios e mantenha cordialidade nas respostas.",
                    "Quando email e telefone estiverem confirmados, mude next_stage para 'qualification' sem permanecer neste estágio.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.QUALIFICATION: Agent(
                name="Qualification Agent",
                instructions=[
                    "Você avalia a renda mensal e necessidades do cliente.",
                    "Explique por que cada informação é importante e seja consultivo.",
                    "Considere qualificar leads com renda ≥ R$ 5.000.",
                    "Após coletar renda e principais necessidades, defina next_stage conforme qualificação: 'conversion' para qualificados ou 'nurturing' para não qualificados.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.OBJECTION_HANDLING: Agent(
                name="Objection Handling Agent",
                instructions=[
                    "Você trata objeções sobre preço, confiança ou tempo com empatia.",
                    "Valide a preocupação, ofereça solução específica e retome o fluxo.",
                    "Mantenha foco em benefícios concretos dos serviços da Agilize.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.CONVERSION: Agent(
                name="Conversion Agent",
                instructions=[
                    "Você conduz leads qualificados ao fechamento do contrato.",
                    "Apresente proposta clara com valores e próximos passos imediatos.",
                    "Crie urgência positiva e confirme interesse direto.",
                    "Se o cliente confirmar avanço ou solicitar encerramento, ajuste next_stage para 'completed'.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.NURTURING: Agent(
                name="Nurturing Agent",
                instructions=[
                    "Você mantém relacionamento com leads ainda não qualificados.",
                    "Ofereça conteúdos, dicas e mantenha porta aberta para o futuro.",
                    "Seja compreensivo e evite pressão por fechamento imediato.",
                    "Assim que oferecer próximos passos de acompanhamento, encerre definindo next_stage para 'completed'.",
                ]
                + structured_output,
                **base_kwargs,
            ),
            ConversationStage.COMPLETED: Agent(
                name="Completion Agent",
                instructions=[
                    "Você finaliza a conversa reforçando próximos passos e apoio.",
                    "Agradeça o tempo do cliente e confirme ações combinadas.",
                    "Mantenha tom positivo e profissional.",
                ]
                + structured_output,
                **base_kwargs,
            ),
        }

        return agents

    def _structured_output_instructions(self) -> List[str]:
        example_json = (
            '{"extracted": {"nome_completo": "João Silva", "email": "joao@exemplo.com", '
            '"telefone": "71999998888", "renda_mensal": 7500.0}, "next_stage": "qualification"}'
        )
        return [
            "FORMATO DE SAÍDA OBRIGATÓRIO:",
            "1. Responda ao cliente em até 2 frases, em português brasileiro.",
            "2. Na linha seguinte escreva exatamente '---DATA---'.",
            "3. Após o separador, forneça um JSON com as chaves:",
            "   - extracted: objeto com campos relevantes coletados (nome_completo, email, telefone, renda_mensal, etc.)",
            "   - next_stage: estágio sugerido (greeting, data_collection, qualification, conversion, nurturing, objection_handling, completed)",
            f"Exemplo: {example_json}",
            "4. Use null para campos desconhecidos e mantenha valores numéricos quando possível.",
            "5. Analise 'Campos pendentes' do prompt: se todos os dados obrigatórios do estágio atual estiverem completos, defina next_stage para o próximo estágio lógico (ou 'completed' quando apropriado).",
            "6. Nunca mantenha next_stage no mesmo estágio quando não houver dados pendentes desse estágio.",
        ]

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
            except Exception as exc:
                logger.exception("Agent %s failed on stage %s: %s", agent.name, stage.value, exc)
                content = (
                    "Desculpe, estou com dificuldade técnica agora. Pode repetir em alguns instantes?"
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
    def _build_stage_prompt(self, stage: ConversationStage, context: ConversationContext, user_input: str) -> str:
        history = self._get_recent_history(context)
        data_summary = self._render_context_summary(context)
        missing = self._render_missing_data(context)
        objective = self._stage_objective(stage)

        return (
            "Resumo das últimas mensagens:\n"
            f"{history}\n\n"
            "Dados coletados até agora:\n"
            f"{data_summary}\n\n"
            f"Campos pendentes: {missing}\n"
            f"Estágio atual: {stage.value}\n"
            f"Mensagem do cliente: \"{user_input}\"\n\n"
            f"Objetivo imediato: {objective}\n"
            "AVANÇO OBRIGATÓRIO: mantenha a conversa avançando para o próximo dado pendente."
            "Responda seguindo as instruções acima e forneça o bloco '---DATA---' com o JSON atualizado."
        )

    @staticmethod
    def _stage_objective(stage: ConversationStage) -> str:
        mapping = {
            ConversationStage.GREETING: "conseguir nome completo e manter acolhimento",
            ConversationStage.DATA_COLLECTION: "coletar email e telefone válidos",
            ConversationStage.QUALIFICATION: "descobrir renda mensal e necessidades contábeis",
            ConversationStage.OBJECTION_HANDLING: "tratar a objeção apresentada e retomar fluxo",
            ConversationStage.CONVERSION: "confirmar interesse e formalizar próximos passos",
            ConversationStage.NURTURING: "nutrir relacionamento oferecendo valor futuro",
            ConversationStage.COMPLETED: "finalizar a conversa com próximos passos claros",
        }
        return mapping.get(stage, "manter a conversa em andamento")

    @staticmethod
    def _get_recent_history(context: ConversationContext, limit: int = 6) -> str:
        entries = context.messages_exchanged[-limit:]
        if not entries:
            return "(sem mensagens anteriores)"
        rendered = []
        for item in entries:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            rendered.append(f"{role}: {content}")
        return "\n".join(rendered)

    @staticmethod
    def _render_context_summary(context: ConversationContext) -> str:
        lead = context.lead_data
        lines = [
            f"Nome completo: {lead.nome_completo or '[não informado]'}",
            f"Email: {lead.email or '[não informado]'}",
            f"Telefone: {lead.telefone or '[não informado]'}",
            f"Renda mensal: {('R$ %.2f' % lead.renda_mensal) if lead.renda_mensal is not None else '[não informado]'}",
            f"Empresa: {lead.empresa or '[não informado]'}",
            f"Cargo: {lead.cargo or '[não informado]'}",
            f"Tem empresa?: {lead.tem_empresa if lead.tem_empresa is not None else '[não informado]'}",
            f"Precisa contabilidade?: {lead.precisa_contabilidade if lead.precisa_contabilidade is not None else '[não informado]'}",
        ]
        if context.qualification_reason:
            lines.append(f"Status de qualificação: {context.qualification_reason}")
        return "\n".join(lines)

    @staticmethod
    def _render_missing_data(context: ConversationContext) -> str:
        missing = []
        if not context.lead_data.nome_completo:
            missing.append("nome completo")
        if not context.lead_data.email:
            missing.append("email")
        if not context.lead_data.telefone:
            missing.append("telefone")
        if context.lead_data.renda_mensal is None:
            missing.append("renda mensal")
        return ", ".join(missing) if missing else "nenhum"

    # ------------------------------------------------------------------
    # Post-processing & context management
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

    def _update_context_with_extracted_data(self, context: ConversationContext, extracted: Dict[str, Any]) -> None:
        if not extracted:
            return

        lead = context.lead_data
        for field, value in extracted.items():
            if value in (None, ""):
                continue

            parsed_value: Any = value
            if field == "renda_mensal":
                parsed_value = self._parse_income(value)
            elif field == "telefone":
                parsed_value = self._normalize_phone(value)
            elif field in {"tem_empresa", "precisa_contabilidade"}:
                parsed_value = self._parse_bool(value)

            if parsed_value is None:
                continue

            current = getattr(lead, field, None)
            if current == parsed_value:
                continue

            setattr(lead, field, parsed_value)
            if context.fields_collected is None:
                context.fields_collected = []
            if field not in context.fields_collected:
                context.fields_collected.append(field)

        if extracted.get("renda_mensal") is not None:
            context.check_qualification()

    @staticmethod
    def _parse_income(raw_value: Any) -> Optional[float]:
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        if isinstance(raw_value, str):
            cleaned = raw_value.lower()
            cleaned = cleaned.replace("r$", "").replace("reais", "")
            cleaned = cleaned.replace("mil", "000")
            cleaned = re.sub(r"[^0-9,\. ]", "", cleaned)
            cleaned = cleaned.replace(".", "").replace(",", ".").strip()
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_phone(raw_value: Any) -> Optional[str]:
        text = str(raw_value)
        digits = re.sub(r"\D", "", text)
        return digits or None

    @staticmethod
    def _parse_bool(raw_value: Any) -> Optional[bool]:
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)):
            return raw_value != 0
        if isinstance(raw_value, str):
            normalized = raw_value.strip().lower()
            if normalized in {"sim", "true", "yes", "1"}:
                return True
            if normalized in {"não", "nao", "false", "no", "0"}:
                return False
        return None

    def _apply_stage_transition(
        self,
        context: ConversationContext,
        previous_stage: ConversationStage,
        suggested_stage: Optional[ConversationStage],
    ) -> None:
        stage_order = [
            ConversationStage.GREETING,
            ConversationStage.DATA_COLLECTION,
            ConversationStage.QUALIFICATION,
            ConversationStage.CONVERSION,
            ConversationStage.NURTURING,
            ConversationStage.OBJECTION_HANDLING,
            ConversationStage.COMPLETED,
        ]

        computed = self._determine_primary_stage(context)

        if suggested_stage in {
            ConversationStage.COMPLETED,
            ConversationStage.OBJECTION_HANDLING,
        }:
            context.stage = suggested_stage
            return

        if suggested_stage and suggested_stage not in {
            ConversationStage.OBJECTION_HANDLING,
            ConversationStage.COMPLETED,
        }:
            try:
                if stage_order.index(suggested_stage) > stage_order.index(computed):
                    context.stage = suggested_stage
                    return
            except ValueError:
                logger.warning("Ignoring invalid suggested stage: %s", suggested_stage)

        context.stage = computed

    def _determine_primary_stage(self, context: ConversationContext) -> ConversationStage:
        lead = context.lead_data
        if context.stage == ConversationStage.COMPLETED:
            return ConversationStage.COMPLETED
        if not lead.nome_completo:
            return ConversationStage.GREETING
        if not lead.email or not lead.telefone:
            return ConversationStage.DATA_COLLECTION
        if lead.renda_mensal is None:
            return ConversationStage.QUALIFICATION
        if lead.renda_mensal >= 5000:
            context.is_qualified = True
            context.qualification_reason = (
                f"Qualificado: renda mensal de R$ {lead.renda_mensal:,.2f}"
            )
            return ConversationStage.CONVERSION
        context.is_qualified = False
        context.qualification_reason = (
            f"Não qualificado: renda mensal de R$ {lead.renda_mensal:,.2f} (mínimo R$ 5.000)"
        )
        return ConversationStage.NURTURING

    def _trim_history(self, context: ConversationContext, limit: int = 40) -> None:
        if len(context.messages_exchanged) > limit:
            context.messages_exchanged = context.messages_exchanged[-limit:]

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def _route_conversation_state(self, step_input: StepInput) -> List[Steps]:
        context = self._ensure_context()
        user_input = step_input.message or self._latest_user_input
        text = str(user_input).lower()

        if self._detect_completion_request(text):
            context.stage = ConversationStage.COMPLETED
            self._store_context_in_state()
            return [self._stage_steps[ConversationStage.COMPLETED]]

        if self._detect_objection(text):
            context.stage = ConversationStage.OBJECTION_HANDLING
            self._store_context_in_state()
            return [self._stage_steps[ConversationStage.OBJECTION_HANDLING]]

        stage = self._determine_primary_stage(context)
        context.stage = stage
        self._store_context_in_state()

        return [self._stage_steps.get(stage, self._stage_steps[ConversationStage.GREETING])]

    @staticmethod
    def _detect_objection(text: str) -> bool:
        objection_keywords = [
            "caro",
            "muito caro",
            "sem dinheiro",
            "não tenho dinheiro",
            "nao tenho dinheiro",
            "preciso pensar",
            "vou pensar",
            "não quero",
            "nao quero",
            "não preciso",
            "nao preciso",
            "ligação",
            "telefone",
            "dúvida",
            "duvida",
            "não confio",
            "nao confio",
            "golpe",
            "fraude",
        ]
        return any(keyword in text for keyword in objection_keywords)

    @staticmethod
    def _detect_completion_request(text: str) -> bool:
        completion_keywords = [
            "obrigado",
            "muito obrigado",
            "valeu",
            "tchau",
            "até mais",
            "ate mais",
            "finalize",
            "encerre",
            "já recebi",
            "ja recebi",
            "não preciso mais",
            "nao preciso mais",
            "já tenho",
            "ja tenho",
            "já resolvi",
            "ja resolvi",
        ]
        return any(keyword in text for keyword in completion_keywords)

    # ------------------------------------------------------------------
    # Session state & persistence helpers
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
        self._ensure_session_loaded()
        context_data = None

        if self.workflow_session_state and "context" in self.workflow_session_state:
            context_data = self.workflow_session_state.get("context")
        elif self.workflow_session and self.workflow_session.session_data:
            session_data = self.workflow_session.session_data
            context_data = session_data.get("context")
            stored_state = session_data.get("session_state")
            if stored_state:
                self.workflow_session_state = stored_state

        if context_data:
            try:
                self._context = ConversationContext(**context_data)
            except Exception as exc:
                logger.warning("Failed to hydrate context from storage: %s", exc)
                self._context = ConversationContext()
        else:
            self._context = ConversationContext()

        self._store_context_in_state()

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
            self._store_context_in_state()

    def _store_context_in_state(self) -> None:
        if self._context is None:
            self._context = ConversationContext()
        if self.workflow_session_state is None:
            self.workflow_session_state = {}
        self.workflow_session_state["context"] = self._serialize_context(self._context)

    def _persist_context(self, context: ConversationContext) -> None:
        self._context = context
        self._store_context_in_state()
        self._ensure_session_loaded()
        if self.workflow_session is not None:
            if self.workflow_session.session_data is None:
                self.workflow_session.session_data = {}
            self.workflow_session.session_data["context"] = self._serialize_context(context)
            self.workflow_session.session_data["session_state"] = dict(self.session_state)
        self.write_to_storage()

    def _ensure_session_loaded(self) -> None:
        if self.workflow_session is None:
            self.load_session()

    def get_workflow_session(self):  # type: ignore[override]
        session = super().get_workflow_session()
        session_data = dict(session.session_data or {})
        session_data["context"] = self._serialize_context(self._context or ConversationContext())
        session_data["session_state"] = dict(self.session_state)
        session.session_data = session_data
        return session

    def load_workflow_session(self, session):  # type: ignore[override]
        super().load_workflow_session(session)
        session_state = {}
        if session.session_data:
            session_state = session.session_data.get("session_state") or {}
        self.workflow_session_state = session_state

        context_data = None
        if session.session_data:
            context_data = session.session_data.get("context")

        if context_data:
            try:
                self._context = ConversationContext(**context_data)
            except Exception as exc:
                logger.warning("Could not hydrate context from storage: %s", exc)
                self._context = ConversationContext()
        else:
            self._context = ConversationContext()

        self._store_context_in_state()

    def _save_session_state(self) -> None:
        context_data = self.session_state.get("context") if self.session_state else None
        if context_data:
            try:
                context = ConversationContext(**context_data)
            except Exception:
                context = ConversationContext()
        else:
            context = ConversationContext()

        self._context = context
        self._persist_context(context)

    def _get_context(self) -> ConversationContext:
        return self._ensure_context()

    def reset(self) -> None:
        self.session_state.clear()
        self._context = ConversationContext()
        self._persist_context(self._context)

    @staticmethod
    def _serialize_context(context: ConversationContext) -> Dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {key: convert(val) for key, val in value.items()}
            return value

        return convert(context.model_dump())

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
        except Exception as exc:
            logger.exception("State machine execution failed: %s", exc)
            fallback = (
                "Desculpe, ocorreu um erro. Nossa equipe técnica foi notificada. Tente novamente em instantes."
            )
            yield RunResponse(content=fallback)
        finally:
            if self._context is not None:
                self._save_session_state()
            self._latest_user_input = ""

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
