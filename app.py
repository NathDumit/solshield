"""Rodar a API localmente: python app.py  (http://localhost:5000)

O modo debug do Flask permite executar código pelo navegador, então fica
desligado por padrão. Para ligar só na sua máquina: FLASK_DEBUG=1 python app.py
"""
import os

from api.index import app

if __name__ == "__main__":
    app.run(port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
