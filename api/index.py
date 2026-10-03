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

from flask import Flask, jsonify, send_file
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


@app.route("/api/score/<id_transacao>")
def score(id_transacao):
    return jsonify(calcular_risco(id_transacao))


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
