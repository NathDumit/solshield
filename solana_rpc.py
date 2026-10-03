"""
Análise de transações REAIS da Solana (opcional).

Recebe a assinatura de uma transação, busca na rede via RPC e devolve o mesmo
dicionário que o frontend espera (status, score, motivos...).
Só usa a biblioteca padrão do Python (sem pip install extra).

Variável de ambiente opcional:
  SOLANA_RPC  -> URL do RPC. Padrão: devnet (https://api.devnet.solana.com)
                 Para mainnet: https://api.mainnet-beta.solana.com
                 (ou uma URL gratuita da Helius/QuickNode, com chave)

As regras abaixo são HEURÍSTICAS simples, boas para demonstração.
"""
import json
import os
import urllib.request

RPC_URL = os.environ.get("SOLANA_RPC", "https://api.devnet.solana.com")

PROGRAMAS_CONHECIDOS = {
    "11111111111111111111111111111111",              # System Program
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",   # SPL Token
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",   # Token-2022
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",  # Associated Token
    "ComputeBudget111111111111111111111111111111",   # Compute Budget
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",   # Memo v1
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",   # Memo v2
}
PROGRAMAS_TOKEN = ("spl-token", "spl-token-2022")
BASE58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def parece_assinatura(texto):
    """Assinaturas da Solana têm ~88 caracteres base58."""
    return 80 <= len(texto) <= 90 and all(c in BASE58 for c in texto)


def _rpc(metodo, params):
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=corpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _curto(chave):
    return chave[:4] + "…" + chave[-4:]


def analisar(assinatura):
    """Retorna o dicionário de risco, ou None se a transação não for encontrada."""
    resp = _rpc("getTransaction", [assinatura, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 0,
        "commitment": "confirmed",
    }])
    tx = resp.get("result")
    if not tx:
        return None

    msg = tx["transaction"]["message"]
    meta = tx.get("meta") or {}
    instrucoes = list(msg.get("instructions", []))
    for grupo in meta.get("innerInstructions") or []:
        instrucoes += grupo.get("instructions", [])

    pagador = msg["accountKeys"][0]["pubkey"]
    saldo_antes = (meta.get("preBalances") or [0])[0]
    saldo_depois = (meta.get("postBalances") or [0])[0]

    motivos = []
    score = 0
    total_enviado = 0          # lamports enviados por instruções "transfer" do System Program
    desconhecidos = set()
    tipos = []

    for ins in instrucoes:
        programa, pid, parsed = ins.get("program"), ins.get("programId"), ins.get("parsed")
        if pid not in PROGRAMAS_CONHECIDOS:
            desconhecidos.add(pid)
            continue
        if not isinstance(parsed, dict):
            continue
        tipo, info = parsed.get("type"), parsed.get("info") or {}
        tipos.append(f"{programa}:{tipo}")

        if programa in PROGRAMAS_TOKEN:
            if tipo == "setAuthority":
                if info.get("authorityType") in ("accountOwner", "closeAccount"):
                    score += 70
                    motivos.append({"nivel": "alto", "texto": "Troca o dono de uma conta de token: quem receber passa a controlar os fundos dela."})
                else:
                    score += 45
                    motivos.append({"nivel": "alto", "texto": "Muda uma autoridade do token (" + str(info.get("authorityType")) + ")."})
            elif tipo in ("approve", "approveChecked"):
                bruto = info.get("amount") or (info.get("tokenAmount") or {}).get("amount") or "0"
                if int(bruto) >= 10 ** 15:
                    score += 45
                    motivos.append({"nivel": "alto", "texto": "Aprova um valor praticamente ilimitado: o destinatário poderá mover todo o token."})
                else:
                    score += 20
                    motivos.append({"nivel": "medio", "texto": "Dá permissão para outro endereço movimentar seus tokens."})
            elif tipo == "closeAccount":
                score += 10
                motivos.append({"nivel": "baixo", "texto": "Fecha uma conta de token."})
        elif programa == "system":
            if tipo == "assign":
                score += 60
                motivos.append({"nivel": "alto", "texto": "Troca o programa dono de uma conta: pode entregar o controle dela a terceiros."})
            elif tipo in ("transfer", "transferWithSeed"):
                total_enviado += int(info.get("lamports") or 0)

    if total_enviado and saldo_antes:
        proporcao = total_enviado / saldo_antes
        sol = total_enviado / 1e9
        if proporcao >= 0.9:
            score += 70  # esvaziar a carteira sozinho já é risco crítico
            motivos.append({"nivel": "alto", "texto": f"Envia {sol:.4f} SOL, mais de 90% do saldo da carteira."})
        elif proporcao >= 0.5:
            score += 30
            motivos.append({"nivel": "medio", "texto": f"Envia {sol:.4f} SOL, mais da metade do saldo da carteira."})
        else:
            motivos.append({"nivel": "ok", "texto": f"Envia {sol:.4f} SOL, uma parte pequena do saldo."})

    if desconhecidos:
        score += min(25, 10 * len(desconhecidos))
        lista = ", ".join(_curto(p) for p in sorted(x for x in desconhecidos if x))
        motivos.append({"nivel": "medio", "texto": f"Interage com {len(desconhecidos)} programa(s) não verificado(s): {lista}."})

    if meta.get("err"):
        motivos.append({"nivel": "baixo", "texto": "Esta transação falhou na rede."})
    if not motivos:
        motivos.append({"nivel": "ok", "texto": "Apenas instruções comuns e conhecidas."})

    score = min(100, score)
    status = "Red" if score >= 70 else "Yellow" if score >= 35 else "Green"
    if total_enviado:
        acao = f"Enviar {total_enviado / 1e9:.4f} SOL e executar {len(instrucoes)} instrução(ões) na Solana."
    else:
        acao = f"Executar {len(instrucoes)} instrução(ões) na Solana."

    return {
        "status": status,
        "score": score,
        "site": "carteira " + _curto(pagador),
        "acao": acao,
        "permissao": ", ".join(dict.fromkeys(tipos)) or "instruções diversas",
        "taxa": f"{(meta.get('fee') or 0) / 1e9:.6f} SOL",
        "saldo_antes": round(saldo_antes / 1e9, 4),
        "saldo_depois": round(saldo_depois / 1e9, 4),
        "motivos": motivos,
    }


# ---------------------------------------------------------------------------
# ANÁLISE ANTES DA ASSINATURA
# A carteira ainda não assinou nada. Consultamos a rede para saber o saldo de
# quem envia e o histórico de quem recebe, e calculamos o risco da transferência.
# ---------------------------------------------------------------------------
SYSTEM_PROGRAM = "11111111111111111111111111111111"
TAXA_LAMPORTS = 5000  # taxa base de uma transferência simples


def parece_endereco(texto):
    """Endereços da Solana têm de 32 a 44 caracteres base58."""
    return 32 <= len(texto) <= 44 and all(c in BASE58 for c in texto)


LIMITE_HISTORICO = 200  # quantas transações recentes olhamos de cada carteira


def _denunciadas():
    try:
        from denuncias import todas
        return todas()
    except Exception:
        return {}


def _reputacao(origem, destino, historico):
    """Quatro checagens sobre quem vai receber. Devolve (pontos, motivos)."""
    import time
    pontos, motivos = 0, []
    lista = _denunciadas()

    # 1) Lista de endereços denunciados
    if destino in lista:
        pontos += 80
        motivos.append({"nivel": "alto", "texto": "O destino está na nossa lista de endereços denunciados: " + str(lista[destino]) + "."})

    # Só dá para saber a idade e a origem se enxergamos o histórico inteiro
    completo = 0 < len(historico) < LIMITE_HISTORICO
    mais_antiga = historico[-1] if completo else None

    # 2) Idade da carteira (data da primeira transação)
    if mais_antiga and mais_antiga.get("blockTime"):
        horas = (time.time() - mais_antiga["blockTime"]) / 3600
        if horas < 24:
            pontos += 15
            motivos.append({"nivel": "medio", "texto": "A carteira de destino foi criada há menos de 24 horas."})
        elif horas < 24 * 7:
            pontos += 5
            motivos.append({"nivel": "baixo", "texto": f"A carteira de destino é recente: {int(horas // 24)} dia(s) de uso."})
        else:
            motivos.append({"nivel": "ok", "texto": f"A carteira de destino existe há {int(horas // 24)} dias."})

    # 3) Origem dos fundos: quem pagou a primeira transação dessa carteira
    if mais_antiga and mais_antiga.get("signature"):
        tx = _rpc("getTransaction", [mais_antiga["signature"], {
            "encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}]).get("result")
        if tx:
            financiador = tx["transaction"]["message"]["accountKeys"][0]["pubkey"]
            if financiador in lista:
                pontos += 40
                motivos.append({"nivel": "alto", "texto": "Quem financiou essa carteira está na lista de endereços denunciados."})
            elif financiador == origem:
                motivos.append({"nivel": "ok", "texto": "Os primeiros fundos dessa carteira vieram de você."})
            elif financiador != destino:
                motivos.append({"nivel": "baixo", "texto": "Os primeiros fundos dessa carteira vieram de " + _curto(financiador) + "."})

    # 4) Relação entre as duas carteiras: já transacionaram antes?
    if historico and destino != origem:
        minhas = _rpc("getSignaturesForAddress", [origem, {"limit": LIMITE_HISTORICO}]).get("result") or []
        em_comum = {x.get("signature") for x in minhas} & {x.get("signature") for x in historico}
        if em_comum:
            pontos -= 15
            motivos.append({"nivel": "ok", "texto": f"Você já transacionou com esta carteira {len(em_comum)} vez(es)."})
        else:
            motivos.append({"nivel": "baixo", "texto": "É a primeira vez que você transaciona com esta carteira."})

    return pontos, motivos


def prever(origem, destino, valor_sol):
    """Risco de enviar valor_sol de origem para destino, ANTES de assinar."""
    lamports = int(round(valor_sol * 1e9))
    saldo = int((_rpc("getBalance", [origem]).get("result") or {}).get("value") or 0)
    conta = (_rpc("getAccountInfo", [destino, {"encoding": "base64"}]).get("result") or {}).get("value")
    historico = _rpc("getSignaturesForAddress", [destino, {"limit": LIMITE_HISTORICO}]).get("result") or []

    motivos = []
    score = 0

    if lamports + TAXA_LAMPORTS > saldo:
        return {"erro": f"Saldo insuficiente: a carteira tem {saldo / 1e9:.4f} SOL."}

    proporcao = lamports / saldo if saldo else 1
    if proporcao >= 0.9:
        score += 70
        motivos.append({"nivel": "alto", "texto": f"Envia {valor_sol:.4f} SOL, mais de 90% do saldo: a carteira fica praticamente vazia."})
    elif proporcao >= 0.5:
        score += 30
        motivos.append({"nivel": "medio", "texto": f"Envia {valor_sol:.4f} SOL, mais da metade do saldo da carteira."})
    else:
        motivos.append({"nivel": "ok", "texto": f"Envia {valor_sol:.4f} SOL, uma parte pequena do saldo."})

    if destino == origem:
        motivos.append({"nivel": "baixo", "texto": "O destino é a sua própria carteira."})
    elif conta and conta.get("executable"):
        score += 40
        motivos.append({"nivel": "alto", "texto": "O destino é um programa, não uma carteira de pessoa."})
    elif conta and conta.get("owner") != SYSTEM_PROGRAM:
        score += 25
        motivos.append({"nivel": "medio", "texto": "O destino não é uma carteira comum: é uma conta controlada por um programa."})
    elif not historico:
        score += 25
        motivos.append({"nivel": "medio", "texto": "A carteira de destino nunca foi usada. Carteiras descartáveis são comuns em golpes."})
    elif len(historico) < 5:
        score += 10
        motivos.append({"nivel": "baixo", "texto": f"A carteira de destino tem pouco histórico ({len(historico)} transação(ões))."})
    else:
        motivos.append({"nivel": "ok", "texto": "A carteira de destino já tem histórico de uso na rede."})

    # Reputação da carteira de destino. Se alguma consulta extra falhar,
    # a análise básica acima continua valendo.
    try:
        pontos, extras = _reputacao(origem, destino, historico)
        score += pontos
        motivos += extras
    except Exception:
        pass

    score = max(0, min(100, score))
    status = "Red" if score >= 70 else "Yellow" if score >= 35 else "Green"
    return {
        "status": status,
        "score": score,
        "previa": True,
        "site": "destino " + _curto(destino),
        "acao": f"Enviar {valor_sol:.4f} SOL da sua carteira para {_curto(destino)}.",
        "permissao": "system:transfer",
        "taxa": f"{TAXA_LAMPORTS / 1e9:.6f} SOL (estimada)",
        "saldo_antes": round(saldo / 1e9, 4),
        "saldo_depois": round((saldo - lamports - TAXA_LAMPORTS) / 1e9, 4),
        "motivos": motivos,
    }
