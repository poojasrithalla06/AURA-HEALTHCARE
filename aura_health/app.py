from flask import Flask
from aura_health.models.database import db
from aura_health.routes.auth_routes import auth_bp
from aura_health.routes.main_routes import main_bp
from aura_health.routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'aura_health_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aura_health.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    print("🔥 AuraHealth Server Starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)