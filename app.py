from flask import Flask
import logging
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize DB
    db.init_app(app)

    with app.app_context():
        import models
        db.create_all()
        logger.info("Database tables created successfully")

        # Create default admin & delivery users
        from models import User
        from auth import hash_password
        from config import Config

        admin_user = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if not admin_user:
            admin = User(
                username=Config.ADMIN_USERNAME,
                password_hash=hash_password(Config.ADMIN_PASSWORD),
                role='admin',
                full_name='Admin User',
                is_active=True
            )
            db.session.add(admin)
            logger.info("Admin user created")

        delivery_user = User.query.filter_by(username=Config.DELIVERY_USERNAME).first()
        if not delivery_user:
            delivery = User(
                username=Config.DELIVERY_USERNAME,
                password_hash=hash_password(Config.DELIVERY_PASSWORD),
                role='delivery',
                full_name='Delivery Person',
                is_active=True
            )
            db.session.add(delivery)
            logger.info("Delivery user created")

        db.session.commit()

        # Import and register blueprints
        from routes import main_bp, admin_bp, delivery_bp, customer_bp, support_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(delivery_bp, url_prefix='/delivery')
        app.register_blueprint(customer_bp, url_prefix='/customer')
        app.register_blueprint(support_bp, url_prefix='/support')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

