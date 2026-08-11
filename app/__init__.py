from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from config import Config


def create_app():
    static_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    )

    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

    from app.routes import main
    app.register_blueprint(main)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        if path and os.path.isfile(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")

    return app
