from agno.tools import tool
from typing import Dict, Optional
from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse, get_all_nfse

@tool(show_result=True, stop_after_tool_call=False)
def emitir_nfse_tool(nome: str, valor: str, descricao: str, cnae: str, item_servico: str) -> str:
    """Emite uma nota fiscal de serviço eletrônica.
    
    IMPORTANTE: Use esta ferramenta APENAS depois de ter todos os parâmetros obrigatórios.
    Se o usuário mencionar 'como a anterior' ou 'igual ao cliente X', 
    PRIMEIRO busque os dados usando buscar_nfse_tool ou get_all_nfse_tool.
    
    Args:
        nome: Nome do cliente (obrigatório)
        valor: Valor da nota fiscal (obrigatório)
        descricao: Descrição dos serviços prestados (obrigatório)
        cnae: Código CNAE da atividade (obrigatório)
        item_servico: Código do item de serviço municipal (obrigatório)
    
    Returns:
        Confirmação da emissão da NFS-e
    """
    params = {
        'nome': nome,
        'valor': valor,
        'descricao': descricao,
        'cnae': cnae,
        'item_servico': item_servico
    }
    return emitir_nfse(params)

@tool(show_result=True, stop_after_tool_call=False)
def buscar_nfse_tool(id_nfse: Optional[str] = None, numero: Optional[str] = None, 
                     nome: Optional[str] = None, status: Optional[str] = None) -> str:
    """Busca notas fiscais eletrônicas por diferentes filtros.
    
    USAR PARA: Encontrar dados de notas anteriores para reutilizar em novas emissões.
    Ideal quando o usuário menciona cliente específico: 'como a nota do João', 'igual ao cliente Maria'.
    
    Args:
        id_nfse: ID específico da nota fiscal (opcional)
        numero: Número da nota fiscal (opcional)
        nome: Nome do cliente - USE ESTE para buscar notas de cliente específico (opcional)
        status: Status da nota fiscal (opcional)
    
    Returns:
        Lista detalhada de notas fiscais encontradas com todos os dados (nome, valor, descrição, CNAE, item_servico)
    """
    params = {}
    if id_nfse:
        params['id_nfse'] = id_nfse
    if numero:
        params['numero'] = numero
    if nome:
        params['nome'] = nome
    if status:
        params['status'] = status
    
    return buscar_nfse(params)

@tool(show_result=True, stop_after_tool_call=False)
def cancelar_nfse_tool(id_nfse: Optional[str] = None, numero: Optional[str] = None) -> str:
    """Cancela uma nota fiscal de serviço eletrônica.
    
    Args:
        id_nfse: ID da nota fiscal (opcional)
        numero: Número da nota fiscal (opcional)
    
    Returns:
        Confirmação do cancelamento da NFS-e
    """
    params = {}
    if id_nfse:
        params['id_nfse'] = id_nfse
    if numero:
        params['numero'] = numero
    
    return cancelar_nfse(params)

@tool(show_result=True, stop_after_tool_call=False)
def get_all_nfse_tool(user_id: Optional[str] = None) -> str:
    """Retorna todas as notas fiscais de um usuário.
    
    USAR PARA: Contexto geral e quando o usuário menciona 'última nota', 'anterior', 'mostrar todas'.
    Ideal para encontrar a nota mais recente quando usuário não especifica cliente.
    
    Args:
        user_id: ID do usuário (opcional)
    
    Returns:
        Lista completa das notas fiscais com todos os detalhes (número, nome, valor, descrição, CNAE, item_servico)
        ordenadas por data (mais recentes primeiro)
    """
    params = {}
    if user_id:
        params['user_id'] = user_id
    
    return get_all_nfse(params)