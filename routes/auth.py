from core.imports import Blueprint, load_dotenv, jsonify

auth_bp = Blueprint('auth', __name__)
load_dotenv()

@auth_bp.route('/account', methods=["GET"])
def get_account():
    return jsonify({"msg": "Gotten account details"})