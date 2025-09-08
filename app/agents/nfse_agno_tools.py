from agno.tools import tool
from typing import Dict, Optional
from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse, get_all_nfse

@tool(show_result=True)
def emitir_nfse_tool(nome: str, valor: str, descricao: str, cnae: str, item_servico: str) -> str:
    """Emite uma nota fiscal de serviço eletrônica.
    
    Args:
        nome: Nome do cliente
        valor: Valor da nota fiscal
        descricao: Descrição dos serviços prestados
        cnae: Código CNAE da atividade
        item_servico: Código do item de serviço municipal
    
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

@tool(show_result=True)
def buscar_nfse_tool(id_nfse: Optional[str] = None, numero: Optional[str] = None, 
                     nome: Optional[str] = None, status: Optional[str] = None) -> str:
    """Busca notas fiscais eletrônicas por diferentes filtros.
    
    Args:
        id_nfse: ID específico da nota fiscal (opcional)
        numero: Número da nota fiscal (opcional)
        nome: Nome do cliente (opcional)
        status: Status da nota fiscal (opcional)
    
    Returns:
        Lista de notas fiscais encontradas
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

@tool(show_result=True)
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

@tool(show_result=True)
def get_all_nfse_tool(user_id: Optional[str] = None) -> str:
    """Retorna todas as notas fiscais de um usuário.
    
    Args:
        user_id: ID do usuário (opcional)
    
    Returns:
        Lista das notas fiscais do usuário
    """
    params = {}
    if user_id:
        params['user_id'] = user_id
    
    return get_all_nfse(params)