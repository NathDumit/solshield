"""
API do SolShield (Flask).
- Local:   python app.py   (porta 5000)
- Vercel:  esta pasta api/ vira uma função serverless automaticamente.
"""
import os
import sys

# Permite importar risk_engine.py / solana_rpc.py que ficam na raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS

from risk_engine import calcular_risco

app = Flask(__name__)
CORS(app)  # permite o frontend acessar de outro endereço


@app.route("/api/score/<id_transacao>")
def score(id_transacao):
    return jsonify(calcular_risco(id_transacao))


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
