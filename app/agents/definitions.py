# Função para buscar notas fiscais de serviço
def get_buscar_nfse_function():
    return {
        "name": "buscar_nfse",
        "description": "Busca notas fiscais de serviço existentes conforme filtros.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome do cliente (opcional)"},
                "numero": {"type": "string", "description": "Número da nota fiscal (opcional)"},
                "status": {"type": "string", "description": "Status da nota (opcional)"}
            }
        }
    }

# Função para cancelar nota fiscal de serviço
def get_cancelar_nfse_function():
    return {
        "name": "cancelar_nfse",
        "description": "Cancela uma nota fiscal de serviço pelo número.",
        "parameters": {
            "type": "object",
            "properties": {
                "numero": {"type": "string", "description": "Número da nota fiscal a ser cancelada"}
            },
            "required": ["numero"]
        }
    }

# Função para emitir nota fiscal de serviço
def get_emitir_nfse_function():
    return {
        "name": "emitir_nfse",
        "description": "Emite uma nota fiscal de serviço (NFS-e) para um cliente.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome do cliente cadastrado no sistema"},
                "valor": {"type": "string", "description": "Valor do serviço"},
                "descricao": {"type": "string", "description": "Descrição detalhada do serviço"},
                "cnae": {"type": "string", "description": "CNAE do serviço"},
                "item_servico": {"type": "string", "description": "Item de serviço conforme tabela municipal"}
            },
            "required": ["nome", "valor", "descricao", "cnae", "item_servico"]
        }
    }

