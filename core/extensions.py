# extensions.py
from core.imports import CORS, Swagger, SQLAlchemy, Mail, Bcrypt, JWTManager, OAuth, Migrate
from itsdangerous import URLSafeTimedSerializer



db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
swagger = Swagger()
cors = CORS()
bcrypt = Bcrypt()
migrate = Migrate()
serializer = URLSafeTimedSerializer("secret_key")
