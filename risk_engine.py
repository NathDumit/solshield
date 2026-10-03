"""
MOTOR DE RISCO.

- tx_001, tx_002 e tx_003 são cenários de DEMONSTRAÇÃO (dados fictícios).
- Se o ID for uma assinatura real da Solana (~88 caracteres), a transação é
  buscada na rede e analisada por solana_rpc.py.
- A pessoa de dados pode substituir/expandir calcular_risco(), mantendo o formato:

  Obrigatório: status ("Green" | "Yellow" | "Red")
  Opcionais (o frontend usa se vierem; senão mostra valores ilustrativos):
    score (0-100), site, acao (frase simples do que a transação faz),
    permissao (ex: "Approve(USDC, ilimitado)"), taxa, saldo_antes, saldo_depois,
    motivos: lista de {"nivel": "alto|medio|baixo|ok", "texto": "..."}
"""

EXEMPLOS = {
    "tx_001": {
        "status": "Green", "score": 8, "site": "jup.ag",
        "acao": "Enviar 0.05 SOL para o programa verificado da Jupiter, para fazer a troca que você pediu.",
        "permissao": "Transfer(0.05 SOL)", "taxa": "0.000005 SOL",
        "saldo_antes": 12.40, "saldo_depois": 12.35,
        "motivos": [
            {"nivel": "ok", "texto": "Domínio verificado, com histórico longo de uso."},
            {"nivel": "ok", "texto": "Contrato auditado e sem funções ocultas."},
        ],
    },
    "tx_002": {
        "status": "Yellow", "score": 54, "site": "swap-rewards.xyz",
        "acao": "Dar permissão para este contrato movimentar seus tokens USDC, sem limite de valor.",
        "permissao": "Approve(USDC, ilimitado)", "taxa": "0.000005 SOL",
        "saldo_antes": 12.40, "saldo_depois": 12.35,
        "motivos": [
            {"nivel": "medio", "texto": "Permissão ilimitada: o contrato poderá mover todo o seu USDC."},
            {"nivel": "medio", "texto": "O site foi criado há apenas 12 dias."},
        ],
    },
    "tx_003": {
        "status": "Red", "score": 97, "site": "free-airdrop-sol.xyz",
        "acao": "Entregar o controle total da sua carteira a um endereço desconhecido, que poderá esvaziá-la a qualquer momento.",
        "permissao": "SetAuthority(dono da carteira)", "taxa": "0.000005 SOL",
        "saldo_antes": 12.40, "saldo_depois": 0.0,
        "motivos": [
            {"nivel": "alto", "texto": "Troca o dono da carteira: terceiros passam a controlar seus fundos."},
            {"nivel": "alto", "texto": "O destino aparece em denúncias de golpe."},
            {"nivel": "alto", "texto": "O site imita um airdrop oficial (phishing)."},
        ],
    },
}


def _desconhecida(motivo):
    # "desconhecida": True avisa o frontend para mostrar só a mensagem,
    # sem nota de risco e sem dados de exemplo.
    return {"status": "Yellow", "score": 50, "desconhecida": True, "mensagem": motivo,
            "motivos": [{"nivel": "medio", "texto": motivo}]}


def _parece_endereco(texto):
    """Endereços de carteira da Solana têm de 32 a 44 caracteres base58."""
    base58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    return 32 <= len(texto) <= 44 and all(c in base58 for c in texto)


def calcular_risco(id_transacao):
    chave = id_transacao.strip().lower()
    if chave in EXEMPLOS:
        return EXEMPLOS[chave]

    try:
        from solana_rpc import parece_assinatura, analisar, RPC_URL
    except ImportError:
        return _desconhecida("Transação desconhecida: sem histórico para analisar.")

    if parece_assinatura(id_transacao.strip()):
        try:
            resultado = analisar(id_transacao.strip())
        except Exception as erro:  # rede fora do ar, limite do RPC etc.
            return _desconhecida("Não foi possível consultar a rede Solana agora (" + str(erro)[:80] + ").")
        if resultado:
            return resultado
        return _desconhecida("Transação não encontrada em " + RPC_URL + ". Confira se a rede (devnet/mainnet) está certa.")

    if _parece_endereco(id_transacao.strip()):
        return _desconhecida("Isso parece um endereço de carteira, não uma transação. Cole a Signature da transação (cerca de 88 caracteres).")
    return _desconhecida("ID não reconhecido. Use tx_001, tx_002, tx_003 ou cole a Signature de uma transação da Solana.")
