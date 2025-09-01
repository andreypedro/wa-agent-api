"""
Agente para emissão de Nota Fiscal de Serviço (NFS-e).
Esta função simula o processo e pode ser adaptada para integração real com APIs municipais.
"""

from typing import Dict

def emitir_nfse(dados: Dict) -> str:
    # Simulação de emissão
    nome = dados.get('nome', 'Cliente')
    valor = dados.get('valor', '0.00')
    descricao = dados.get('descricao', 'Descrição não informada')
    cnae = dados.get('cnae', 'CNAE não informado')
    item_servico = dados.get('item_servico', 'Item de serviço não informado')
    # Aqui você pode integrar com API real e buscar dados do cliente pelo nome
    return (
        f"NFS-e emitida para {nome}.\n"
        f"Descrição: {descricao}\n"
        f"Valor: R$ {valor}\n"
        f"CNAE: {cnae}\n"
        f"Item de serviço: {item_servico}\n"
        f"Status: Emitida com sucesso (simulação)."
    )


def buscar_nfse(id_nfse=None, numero=None, nome=None, status=None) -> str:
    # Simulação de busca
    notas = [
        {
            'numero': '2025001',
            'nome': 'João Silva',
            'valor': '1500.00',
            'descricao': 'Consultoria',
            'cnae': '1234',
            'item_servico': '01.01',
            'status': 'Emitida'
        },
        {
            'numero': '2025002',
            'nome': 'Maria Souza',
            'valor': '800.00',
            'descricao': 'Design gráfico',
            'cnae': '5678',
            'item_servico': '02.02',
            'status': 'Emitida'
        }
    ]
    def match(nota):
        if id_nfse and str(nota['numero']) != str(id_nfse):
            return False
        if numero and str(nota['numero']) != str(numero):
            return False
        if nome and nome.lower() not in nota['nome'].lower():
            return False
        if status and status.lower() != nota['status'].lower():
            return False
        return True
    encontradas = [n for n in notas if match(n)]
    if not encontradas:
        return "Nenhuma NFS-e encontrada com os filtros fornecidos."
    return f"Notas encontradas: {encontradas}"


def cancelar_nfse(id_nfse=None, numero=None) -> str:
    nfse_id = id_nfse or numero or 'Desconhecido'
    return f"Nota fiscal {nfse_id} cancelada com sucesso (simulação)."
