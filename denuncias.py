"""
LISTA DE ENDEREÇOS DENUNCIADOS.

Duas fontes:
1. OFAC (Tesouro dos EUA): endereços Solana sob sanção oficial. O SolShield baixa a
   lista atualizada na hora, deste repositório público que espelha a lista do governo:
   https://github.com/0xB10C/ofac-sanctioned-digital-currency-addresses
   Se a internet falhar, vale a cópia de segurança abaixo (COPIA_OFAC).
2. Lista do time (DENUNCIADAS): endereços que vocês mesmas adicionam.

Formato:  "endereço da carteira": "motivo"
"""
import urllib.request

URL_OFAC = ("https://raw.githubusercontent.com/0xB10C/"
            "ofac-sanctioned-digital-currency-addresses/lists/sanctioned_addresses_SOL.txt")
MOTIVO_OFAC = "endereço sob sanção do OFAC, o órgão de sanções do Tesouro dos EUA"

# Cópia de segurança da lista do OFAC para Solana, conferida em 03/10/2026.
COPIA_OFAC = [
    "42RLPACwZPx3vYYmxSueqsogfynBDqXK298EDsNoyoHi",
    "6wjqWWra8ombzaw6VHrG5xpQ972jCYF6bbHiFCbWmr4U",
    "Fc1EwQUZyTEagaDvA1utHXCcZNyG1x2PLt2DfNu1cJdH",
    "FuCC7GoYwt5TsNTjWL23Xx9UKCvC18chjMEFPL3vJDCC",
]

# Lista do time. Para a demonstração, coloquem aqui uma carteira de teste de vocês
# e digam na banca que é um exemplo.
DENUNCIADAS = {
    # "EnderecoDaCarteiraDeTeste111111111111111111": "exemplo de demonstração (drainer simulado)",
}

_BASE58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
_cache = None


def _baixar_ofac():
    with urllib.request.urlopen(URL_OFAC, timeout=4) as resp:
        linhas = resp.read().decode("utf-8", "ignore").split()
    return [x for x in linhas if 32 <= len(x) <= 44 and all(c in _BASE58 for c in x)]


def todas():
    """Devolve {endereço: motivo} juntando OFAC (ao vivo ou cópia) e a lista do time."""
    global _cache
    if _cache is None:
        try:
            ofac = _baixar_ofac() or COPIA_OFAC
        except Exception:
            ofac = COPIA_OFAC
        _cache = {e: MOTIVO_OFAC for e in ofac}
    return {**_cache, **DENUNCIADAS}
