from core.imports import Flask, load_dotenv, request, jsonify, cloudinary, random, datetime, timedelta, render_template, Message, create_access_token, Client
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt
from core.models import TempUser, User
from routes.auth import auth_bp

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


def send_email(to, subject, body):
    msg = Message(subject=subject, recipients=[to])
    msg.html = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

def send_otp_email(email, otp, purpose="verification"):
    # Customize content based on purpose
    if purpose == "verification":
        subject = "Your Account Verification OTP"
        message = "Welcome to CamelAI! To complete your verification, please use the code below:"
        purpose_title = "Your Verification Code"
    elif purpose == "password_reset":
        subject = "Your Password Reset OTP"
        message = "We received a request to reset your password. Use the code below to proceed:"
        purpose_title = "Password Reset Code"
    else:
        raise ValueError("Invalid OTP purpose.")

    body = render_template(
        'email.html',
        otp=otp,
        message=message,
        purpose_title=purpose_title,
        year=datetime.now().year
    )

    send_email(email, subject, body)


def send_sms_otp(phone, otp):
    account_sid = "your_twilio_sid"
    auth_token = "your_twilio_auth_token"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=f"Your verification code is {otp}.",
        from_="+1234567890",
        to=phone
    )

@app.route('/ping')
def ping():
    return "Pong", 200


@app.route('/api/auth', methods=["POST"])
def auth():
    """
    Request OTP for authentication
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
            phone:
              type: string
              example: "+1234567890"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: OTP sent successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OTP sent to user@example.com"
      400:
        description: Bad Request
        schema:
          type: object
          properties:
            error:
              type: string
    """
    email = request.json.get('email')
    phone = request.json.get('phone')
    password = request.json.get('password')

    if not email or not phone or not password:
        return jsonify({"error": "Incomplete credentials."}), 400

    # Check if user already exists
    existing_user = None
    if email:
        existing_user = User.query.filter_by(email=email).first()
    elif phone:
        existing_user = User.query.filter_by(phone=phone).first()
    
    if existing_user:
        return jsonify({"error": "Account has already been created and verified. Login to continue"}), 400

    try:
        temp_user = None
        if email:
            temp_user = TempUser.query.filter_by(email=email).first()
        elif phone:
            temp_user = TempUser.query.filter_by(phone=phone).first()

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        if not temp_user:
            temp_user = TempUser(email=email, phone=phone, password_hash=password_hash)
            db.session.add(temp_user)

    
        otp = str(random.randint(100000, 999999))
        print(otp)
        temp_user.otp_code = otp
        temp_user.otp_created_at = datetime.utcnow()

        if email:
            send_otp_email(email, otp)
        elif phone:
            send_sms_otp(phone, otp)


        db.session.commit()
        print("Added entry to db")
        
        if email:
            return jsonify({"message": f"OTP sent to {email}"}), 200
        else:
            return jsonify({"message": f"OTP sent to {phone}"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"OTP send failed: {e}")
        return jsonify({"error": "Failed to send OTP. Please try again later."}), 500


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            email:
              type: string
            phone:
              type: string
            otp:
              type: string
    responses:
      200:
        description: OTP verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OTP verified successfully"
      400:
        description: Bad request (invalid or expired OTP)
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
  
    email = request.json.get('email')
    phone = request.json.get('phone')
    otp = request.json.get('otp')

    if not otp or (not email and not phone):
        return jsonify({"error": "OTP and email or phone is required"}), 400

    if email:
        temp_user = TempUser.query.filter_by(email=email, otp_code=otp).first()
    else:
        temp_user = TempUser.query.filter_by(phone=phone, otp_code=otp).first()

    if not temp_user:
        return jsonify({"error": "Invalid email/phone or OTP"}), 404
    
    expiry_time = temp_user.otp_created_at + timedelta(minutes=20)
    if datetime.utcnow() > expiry_time:
        db.session.delete(temp_user)
        db.session.commit()
        return jsonify({"error": "OTP expired. Please request a new one."}), 400

  
    user = User(email=temp_user.email, phone=temp_user.phone, password_hash=temp_user.password_hash)
    db.session.add(user)
    db.session.delete(temp_user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    return jsonify({
        "message": "OTP verified successfully",
        "access_token": access_token,
        "user_id": user.id,
    }), 200


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload a file (image or video) to Cloudinary
    ---
    tags:
      - Upload
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The file to upload (image or video)
    responses:
      200:
        description: Successful upload
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Upload successful"
            url:
              type: string
              example: "https://res.cloudinary.com/demo/image/upload/sample.jpg"
      400:
        description: No file provided
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No file provided"
      500:
        description: Upload error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Some Cloudinary error message"
    """
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
