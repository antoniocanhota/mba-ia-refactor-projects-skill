import logging
import os
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS

import controllers
import database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao")
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
# Sem isso, o Flask ignora os error handlers abaixo e propaga a exceção pro
# debugger interativo sempre que DEBUG=True.
app.config["PROPAGATE_EXCEPTIONS"] = False
CORS(app)

database.init_app(app)


def requer_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not ADMIN_API_KEY:
            return jsonify({"erro": "Rotas administrativas desabilitadas (ADMIN_API_KEY não configurada)"}), 503
        if request.headers.get("X-Admin-Key") != ADMIN_API_KEY:
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.errorhandler(404)
def tratar_nao_encontrado(e):
    return jsonify({"erro": "Recurso não encontrado"}), 404


@app.errorhandler(Exception)
def tratar_erro_inesperado(e):
    logger.exception("Erro não tratado")
    return jsonify({"erro": "Erro interno do servidor"}), 500


app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/busca", "buscar_produtos", controllers.buscar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
app.add_url_rule("/produtos", "criar_produto", controllers.criar_produto, methods=["POST"])
app.add_url_rule("/produtos/<int:id>", "atualizar_produto", controllers.atualizar_produto, methods=["PUT"])
app.add_url_rule("/produtos/<int:id>", "deletar_produto", controllers.deletar_produto, methods=["DELETE"])

app.add_url_rule("/usuarios", "listar_usuarios", controllers.listar_usuarios, methods=["GET"])
app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", controllers.buscar_usuario, methods=["GET"])
app.add_url_rule("/usuarios", "criar_usuario", controllers.criar_usuario, methods=["POST"])
app.add_url_rule("/login", "login", controllers.login, methods=["POST"])

app.add_url_rule("/pedidos", "criar_pedido", controllers.criar_pedido, methods=["POST"])
app.add_url_rule("/pedidos", "listar_todos_pedidos", controllers.listar_todos_pedidos, methods=["GET"])
app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controllers.listar_pedidos_usuario, methods=["GET"])
app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controllers.atualizar_status_pedido, methods=["PUT"])

app.add_url_rule("/relatorios/vendas", "relatorio_vendas", controllers.relatorio_vendas, methods=["GET"])

app.add_url_rule("/health", "health_check", controllers.health_check, methods=["GET"])

app.add_url_rule("/admin/reset-db", "reset_database", requer_admin(controllers.reset_database), methods=["POST"])
app.add_url_rule("/admin/query", "executar_query", requer_admin(controllers.executar_query), methods=["POST"])


@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://localhost:5000")
    logger.info("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
