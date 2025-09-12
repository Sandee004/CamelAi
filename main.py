from core.imports import Flask, load_dotenv, request, jsonify, cloudinary, random, datetime, timedelta, render_template, Message, create_access_token, Client, get_jwt_identity, jwt_required, base64, re
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, migrate
from core.models import TempUser, User, Conversation
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
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    return app

app = create_app()
load_dotenv()
client = Config.client


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
    Request OTP for authentication (login or signup)
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
            phone:
              type: string
              example: "+1234567890"
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

    if not email and not phone:
        return jsonify({"error": "Email or phone is required"}), 400

    try:
        # Look up existing user
        existing_user = None
        if email:
            existing_user = User.query.filter_by(email=email).first()
        elif phone:
            existing_user = User.query.filter_by(phone=phone).first()

        if existing_user:
            # If user exists, create/update OTP in TempUser table
            temp_user = TempUser.query.filter_by(
                email=existing_user.email if email else None,
                phone=existing_user.phone if phone else None
            ).first()
        else:
            # If new user, create TempUser record
            temp_user = None
            if email:
                temp_user = TempUser.query.filter_by(email=email).first()
            elif phone:
                temp_user = TempUser.query.filter_by(phone=phone).first()
            if not temp_user:
                temp_user = TempUser(email=email, phone=phone)
                db.session.add(temp_user)

        # Always set a new OTP
        otp = str(random.randint(100000, 999999))
        print(f"Generated OTP: {otp}")
        temp_user.otp_code = otp
        temp_user.otp_created_at = datetime.utcnow()

        # Send OTP
        if email:
            send_otp_email(email, otp)
        elif phone:
            send_sms_otp(phone, otp)

        db.session.commit()

        return jsonify({"message": f"OTP sent to {email or phone}"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"OTP send failed: {e}")
        return jsonify({"error": "Failed to send OTP. Please try again later."}), 500


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and login/signup user
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - otp
          properties:
            email:
              type: string
            phone:
              type: string
            otp:
              type: string
              example: "123456"
    responses:
      200:
        description: OTP verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OTP verified successfully"
            access_token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            user_id:
              type: integer
              example: 1
      400:
        description: Invalid or expired OTP
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
        return jsonify({"error": "OTP and email/phone are required"}), 400

    # Find temp_user by OTP
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

    # If user already exists, just fetch it
    user = None
    if temp_user.email:
        user = User.query.filter_by(email=temp_user.email).first()
    elif temp_user.phone:
        user = User.query.filter_by(phone=temp_user.phone).first()

    # Otherwise, create new user
    if not user:
        user = User(email=temp_user.email, phone=temp_user.phone)
        db.session.add(user)

    # Clean up temp user
    db.session.delete(temp_user)
    db.session.commit()

    # Issue token valid for 30 days
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=30))

    return jsonify({
        "message": "OTP verified successfully",
        "access_token": access_token,
        "user_id": user.id,
    }), 200


@app.route('/api/rate-image', methods=["POST"])
@jwt_required(optional=True)
def rate_image():
    """
    Rate an uploaded image using OpenAI Vision model.
    ---
    tags:
      - AI
    consumes:
      - multipart/form-data
    parameters:
      - in: header
        name: Authorization
        type: string
        required: false
        description: "JWT access token. Format: Bearer <token>"
      - in: formData
        name: image
        type: file
        required: true
        description: "Image file to rate"
    responses:
      200:
        description: Rating returned successfully
        schema:
          type: object
          properties:
            rating:
              type: string
              example: "8/10"
      400:
        description: Bad Request
        schema:
          type: object
          properties:
            error:
              type: string
      401:
        description: Unauthorized (invalid token)
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Server Error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    user_id = get_jwt_identity()

    try:
        # If logged in → upload to Cloudinary
        if user_id:
            upload_result = cloudinary.uploader.upload(image_file)
            image_url = upload_result['secure_url']
        else:
            # Guests → base64 encode in data URI
            image_file.seek(0)
            image_url = f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode()}"

        # Send to OpenAI vision model
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Rate this on a scale of 1-10"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        )

        raw_rating = response.choices[0].message.content

        # Extract clean "X/10" format
        match = re.search(r'(\d{1,2})\s*/\s*10', raw_rating)
        if match:
            rating = f"{match.group(1)}/10"
        else:
            rating = raw_rating.strip()

        # Save conversation if logged in
        if user_id:
            convo = Conversation(
                user_id=user_id,
                prompt="Rate this on a scale of 1-10",
                response=rating,
                image_url=image_url
            )
            db.session.add(convo)
            db.session.commit()

        return jsonify({"rating": rating}), 200

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "Failed to process image"}), 500


"""
@app.route('/api/rate-image', methods=["POST"])
def rate_image():
    ""
    Rate an uploaded image using OpenAI Vision model.
    ---
    tags:
      - AI
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: image
        type: file
        required: true
    responses:
      200:
        description: Rating returned successfully
        schema:
          type: object
          properties:
            rating:
              type: string
              example: "8/10"
      400:
        description: Bad Request
        schema:
          type: object
          properties:
            error:
              type: string
    ""
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    
    try:
        # Send to OpenAI vision model
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Rate this on a scale of 1-10"},
                        {"type": "image", "image": image_file.read()}
                    ]
                }
            ]
        )

        rating = response.choices[0].message["content"]
        return jsonify({"rating": rating}), 200

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "Failed to process image"}), 500


""
@app.route("/upload", methods=["POST"])
def upload_file():
    ""
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
    ""
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
"""

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
