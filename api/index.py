"""
API do SolShield (Flask).
- Local:   python app.py   (porta 5000)
- Vercel:  o Flask atende o site inteiro (a página e a API).
"""
import os
import sys

# Pasta raiz do projeto (onde ficam index.html, risk_engine.py e solana_rpc.py)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from risk_engine import calcular_risco

app = Flask(__name__)
CORS(app)  # permite o frontend acessar de outro endereço


@app.route("/")
def pagina():
    """Entrega a página do SolShield (index.html)."""
    caminho = os.path.join(RAIZ, "index.html")
    if not os.path.exists(caminho):
        return "index.html não encontrado ao lado da API.", 404
    return send_file(caminho)


@app.route("/guia")
@app.route("/guia/")
@app.route("/guia.html")
def guia():
    """Entrega o guia para quem nunca usou cripto (guia.html)."""
    caminho = os.path.join(RAIZ, "guia.html")
    if not os.path.exists(caminho):
        return "guia.html não encontrado ao lado da API.", 404
    return send_file(caminho)


@app.route("/api/score/<id_transacao>")
def score(id_transacao):
    return jsonify(calcular_risco(id_transacao))


@app.route("/api/prever")
def prever():
    """Analisa uma transferência ANTES da assinatura: /api/prever?de=...&para=...&valor=0.2"""
    from solana_rpc import parece_endereco, prever as prever_transferencia
    de = (request.args.get("de") or "").strip()
    para = (request.args.get("para") or "").strip()
    try:
        valor = float((request.args.get("valor") or "").replace(",", "."))
    except ValueError:
        valor = 0
    if not parece_endereco(de) or not parece_endereco(para):
        return jsonify({"erro": "Endereço de carteira inválido. Confira origem e destino."})
    if not 0 < valor < 1e9:
        return jsonify({"erro": "Digite um valor em SOL maior que zero."})
    try:
        return jsonify(prever_transferencia(de, para, valor))
    except Exception as erro:  # rede fora do ar, limite do RPC etc.
        return jsonify({"erro": "Não foi possível consultar a rede Solana agora (" + str(erro)[:80] + ")."})


@app.route("/api/explicar", methods=["POST"])
def explicar_rota():
    """Explicação em linguagem simples, escrita por IA, para uma análise já feita.

    Recebe no corpo (JSON) o resultado de /api/score ou /api/prever.
    Opcional: ?idioma=en para a explicação em inglês (padrão: pt).
    Sem chave de IA configurada, responde {"disponivel": false} e o site segue normal.
    """
    from explicacao import explicar
    analise = request.get_json(silent=True)
    idioma = (request.args.get("idioma") or "pt").strip().lower()
    return jsonify(explicar(analise, idioma))


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
