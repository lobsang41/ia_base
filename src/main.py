import os
import sys

# Agrega el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from modules.ai.agent import AI_Agent
from config.settings import SECRET_KEY
from routes import register_routes

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config['SECRET_KEY'] = SECRET_KEY

# Registra rutas desde el módulo routes
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)