"""Rodar a API localmente: python app.py  (http://localhost:5000)"""
from api.index import app

if __name__ == "__main__":
    app.run(port=5000, debug=True)
