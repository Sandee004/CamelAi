from core.imports import Flask, load_dotenv, request, jsonify, cloudinary
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt
from core.models import User
from routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    cors.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp)
    return app

app = create_app()
load_dotenv()


@app.route('/ping')
def ping():
    return "Pong", 200

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    try:
        result = cloudinary.uploader.upload(file, resource_type="auto")
        return jsonify({
            "message": "Upload successful",
            "url": result["secure_url"],
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
