from flask import Flask


def create_app():
    app = Flask(__name__)

    # Import blueprint + reset function
    from .views.routes import api, reset_store

    # IMPORTANT: Reset the in-memory store for each app instance (test isolation)
    reset_store()

    app.register_blueprint(api)
    return app


# Also expose `app` for `flask --app todo run`
app = create_app()