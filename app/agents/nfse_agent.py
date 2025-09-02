"""
Agente para emissão de Nota Fiscal de Serviço (NFS-e).
Esta função simula o processo e pode ser adaptada para integração real com APIs municipais.
"""

from typing import Dict

def emitir_nfse(input: Dict) -> str:
    # Simulação de emissão
    nome = input.get('nome', 'Cliente')
    valor = input.get('valor', '0.00')
    descricao = input.get('descricao', 'Descrição não informada')
    cnae = input.get('cnae', 'CNAE não informado')
    item_servico = input.get('item_servico', 'Item de serviço não informado')
    
    
    return (
        f"NFS-e emitida para {nome}.\n"
        f"Descrição: {descricao}\n"
        f"Valor: R$ {valor}\n"
        f"CNAE: {cnae}\n"
        f"Item de serviço: {item_servico}\n"
        f"Status: Emitida com sucesso (simulação)."
    )


def buscar_nfse(input: Dict) -> str:
    # Simulação de busca
    id_nfse = input.get('id_nfse')
    numero = input.get('numero')
    nome = input.get('nome')
    status = input.get('status')
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
    resultado = []
    for nota in encontradas:
        resultado.append(
            f"Número: {nota['numero']}\n"
            f"Nome: {nota['nome']}\n"
            f"Valor: R$ {nota['valor']}\n"
            f"Descrição: {nota['descricao']}\n"
            f"CNAE: {nota['cnae']}\n"
            f"Item de serviço: {nota['item_servico']}\n"
            f"Status: {nota['status']}\n"
        )

    if(resultado and len(resultado) == 1):
        return "Aqui está a nota encontrada 😎\n\n" + "\n".join(resultado)

    return "Aqui estão as notas encontradas 😄\n\n" + "\n".join(resultado)

def get_all_nfse(input: Dict) -> str:

    user_id = input.get('user_id')

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

    lastNfses = list(reversed(notas))[:5]

    if not lastNfses:
        return "Nenhuma NFS-e emitida até o momento."
    resultado = []
    for nota in lastNfses:
      resultado.append(
         f"Número: {nota['numero']}\n"
         f"Nome: {nota['nome']}\n"
         f"Valor: R$ {nota['valor']}\n"
         f"Descrição: {nota['descricao']}\n"
         f"CNAE: {nota['cnae']}\n"
         f"Item de serviço: {nota['item_servico']}\n"
         f"Status: {nota['status']}\n"
         " "
      )
    return "Ok! Aqui estão as últimas notas emitidas:\n\n" + "\n".join(resultado)


    # Cancel simulation
def cancelar_nfse(input: Dict) -> str:
    id_nfse = input.get('id_nfse')
    numero = input.get('numero')
    nfse_id = id_nfse or numero or 'Desconhecido'
    return f"Nota fiscal {nfse_id} cancelada com sucesso (simulação)."
