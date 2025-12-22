from core.imports import Flask, load_dotenv, request, jsonify, cloudinary, random, datetime, timedelta, render_template, Message, create_access_token, requests, get_jwt_identity, jwt_required, base64, re
from prompt_loader import PromptLoader
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, migrate
from core.models import TempUser, User, Conversation, BeautyResult
from routes.auth import auth_bp
from attribute_weights import calculate_weighted_score, get_all_weights
import imagehash
from PIL import Image
import io

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    
    # Configure CORS with specific settings
    cors.init_app(app, 
                  origins=Config.CORS_ORIGINS,
                  methods=Config.CORS_METHODS,
                  allow_headers=Config.CORS_HEADERS,
                  supports_credentials=True)
    
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    
    # Add OPTIONS handler for all routes to handle CORS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response
    
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
    """Send OTP via SMS - Development mode (disabled)"""
    # Development mode: Skip actual SMS sending
    print(f"[DEV MODE] SMS sending disabled. OTP {otp} would be sent to {phone}")
    return True

def generate_image_hash(image_file):
    """
    Generate a robust, subject-focused hash for camel images that remains consistent
    across resizing, rotation, and minor modifications by focusing on structural features.
    
    Args:
        image_file: File object or file-like object containing image data
    
    Returns:
        str: Combined hash string optimized for subject recognition
    """
    try:
        import cv2
        import numpy as np
        from scipy.spatial.distance import hamming
        
        # Reset file pointer to beginning
        image_file.seek(0)
        
        # Open image with PIL and convert to OpenCV format
        image = Image.open(image_file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Normalize image size to reduce size-dependency (maintain aspect ratio)
        height, width = cv_image.shape[:2]
        target_size = 512
        if width > height:
            new_width = target_size
            new_height = int(height * target_size / width)
        else:
            new_height = target_size
            new_width = int(width * target_size / height)
        
        normalized_image = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Convert to grayscale for feature detection
        gray = cv2.cvtColor(normalized_image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Generate multiple robust hashes
        
        # 1. Enhanced perceptual hash with larger size for more detail
        pil_normalized = Image.fromarray(cv2.cvtColor(normalized_image, cv2.COLOR_BGR2RGB))
        enhanced_phash = imagehash.phash(pil_normalized, hash_size=16)  # Larger hash for more precision
        
        # 2. Wavelet hash (more robust to geometric transformations)
        wavelet_hash = imagehash.whash(pil_normalized, hash_size=16)
        
        # 3. Color hash (captures color distribution)
        color_hash = imagehash.colorhash(pil_normalized, binbits=8)
        
        # 4. Crop-resistant hash (focuses on center content)
        crop_resistant_hash = imagehash.crop_resistant_hash(pil_normalized, hash_size=16)
        
        # 5. Edge-based structural hash
        edges = cv2.Canny(blurred, 50, 150)
        edge_pil = Image.fromarray(edges)
        edge_hash = imagehash.phash(edge_pil, hash_size=12)
        
        # 6. Histogram-based hash for lighting invariance
        hist = cv2.calcHist([blurred], [0], None, [64], [0, 256])
        hist_normalized = cv2.normalize(hist, hist).flatten()
        hist_hash = ''.join([f'{int(x):02x}' for x in hist_normalized[::4]])  # Sample every 4th value
        
        # Combine all hashes with weights (more emphasis on structural features)
        combined_hash = f"{enhanced_phash}_{wavelet_hash}_{color_hash}_{crop_resistant_hash}_{edge_hash}_{hist_hash}"
        
        return combined_hash
        
    except ImportError:
        # Fallback to enhanced PIL-only approach if OpenCV is not available
        print("OpenCV not available, using enhanced PIL-only hashing")
        
        # Reset file pointer
        image_file.seek(0)
        image = Image.open(image_file)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Normalize size
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # Generate enhanced hashes
        enhanced_phash = imagehash.phash(image, hash_size=16)
        wavelet_hash = imagehash.whash(image, hash_size=16)
        color_hash = imagehash.colorhash(image, binbits=8)
        crop_resistant_hash = imagehash.crop_resistant_hash(image, hash_size=16)
        
        # Convert to grayscale for additional structural hash
        gray_image = image.convert('L')
        structural_hash = imagehash.dhash(gray_image, hash_size=12)
        
        combined_hash = f"{enhanced_phash}_{wavelet_hash}_{color_hash}_{crop_resistant_hash}_{structural_hash}"
        
        return combined_hash
        
    except Exception as e:
        print(f"Error generating enhanced image hash: {e}")
        return None
    finally:
        # Reset file pointer for any subsequent use
        image_file.seek(0)


async def validate_camel_image(image_url, async_client):
    """
    Validate if an image contains a camel and if camel parts are clearly visible.
    
    Args:
        image_url: URL of the image to validate
        async_client: AsyncOpenAI client instance
        
    Returns:
        dict: Validation result with success status and detailed feedback
    """
    validation_prompt = """
You are a camel detection expert. Analyze this image and determine:

1. Does this image contain a camel?
2. If yes, are the following camel body parts clearly visible and suitable for beauty analysis?
   - Head (including ears, snout, jaw)
   - Neck 
   - Body (including withers, hump, back)
   - Legs (at least 2-3 legs should be visible)

Provide your response in JSON format with:
{
  "contains_camel": true/false,
  "visible_parts": {
    "head": true/false,
    "neck": true/false, 
    "body": true/false,
    "legs": true/false
  },
  "overall_suitability": true/false,
  "feedback": "Detailed explanation of what you see and why it is/isn't suitable for camel beauty analysis",
  "missing_parts": ["list of missing or poorly visible parts"],
  "quality_issues": ["list of image quality issues if any"]
}

Be strict in your assessment - the image should clearly show a camel with most body parts visible for accurate beauty analysis.
"""
    
    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": validation_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        validation_result = json.loads(response.choices[0].message.content)
        return {
            "success": True,
            "validation": validation_result
        }
        
    except Exception as e:
        print(f"Error in camel validation: {e}")
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "validation": {
                "contains_camel": False,
                "overall_suitability": False,
                "feedback": "Unable to validate image due to technical error"
            }
        }

@app.route('/ping')
def ping():
    return "Pong", 200


@app.route('/api/auth', methods=["POST"])
def auth():
    """
    Request OTP for authentication (login or signup) - Phone only
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
              example: "OTP sent to +1234567890"
      400:
        description: Bad Request
        schema:
          type: object
          properties:
            error:
              type: string
    """
    phone = request.json.get('phone')

    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    try:
        # Look up existing user by phone
        existing_user = User.query.filter_by(phone=phone).first()

        # Always look for or create TempUser record for OTP storage
        temp_user = TempUser.query.filter_by(phone=phone).first()
        if not temp_user:
            temp_user = TempUser(phone=phone)
            db.session.add(temp_user)

        # Always set a new OTP
        otp = str(random.randint(100000, 999999))
        print(f"Generated OTP: {otp}")
        temp_user.otp_code = otp
        temp_user.otp_created_at = datetime.utcnow()

        # Send OTP via SMS
        send_sms_otp(phone, otp)

        db.session.commit()

        return jsonify({"message": f"OTP sent to {phone}"}), 200

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
    phone = request.json.get('phone')
    otp = request.json.get('otp')

    if not otp or not phone:
        return jsonify({"error": "OTP and phone are required"}), 400

    # Development mode: Accept hardcoded OTP '0000'
    if otp == '0000':
        # Find temp_user by phone only (bypass OTP check)
        temp_user = TempUser.query.filter_by(phone=phone).first()
        if not temp_user:
            return jsonify({"error": "Phone number not found. Please request OTP first."}), 404
    else:
        # Find temp_user by phone and OTP
        temp_user = TempUser.query.filter_by(phone=phone, otp_code=otp).first()
        
        if not temp_user:
            return jsonify({"error": "Invalid phone or OTP"}), 404
        
        expiry_time = temp_user.otp_created_at + timedelta(minutes=20)
        if datetime.utcnow() > expiry_time:
            db.session.delete(temp_user)
            db.session.commit()
            return jsonify({"error": "OTP expired. Please request a new one."}), 400

    # If user already exists, just fetch it
    user = User.query.filter_by(phone=temp_user.phone).first()

    # Otherwise, create new user
    if not user:
        user = User(phone=temp_user.phone)
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


@app.route('/api/user/settings', methods=['PUT'])
@jwt_required()
def update_user_settings():
    """
    Update user settings (name, email, phone)
    ---
    tags:
      - User
    consumes:
      - application/json
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: "JWT access token. Format: Bearer <token>"
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            phone:
              type: string
              example: "+1234567890"
    responses:
      200:
        description: User settings updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Settings updated successfully"
            user:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                email:
                  type: string
                phone:
                  type: string
      400:
        description: Bad Request
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
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Get the data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields if provided
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data:
            # Check if email is already taken by another user
            if data['email'] and data['email'] != user.email:
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({"error": "Email already exists"}), 400
            user.email = data['email']
        
        if 'phone' in data:
            # Check if phone is already taken by another user
            if data['phone'] and data['phone'] != user.phone:
                existing_user = User.query.filter_by(phone=data['phone']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({"error": "Phone number already exists"}), 400
            user.phone = data['phone']
        
        db.session.commit()
        
        return jsonify({
            "message": "Settings updated successfully",
            "user": {
                "id": user.id,
                "name": getattr(user, 'name', None),
                "email": user.email,
                "phone": user.phone
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user settings: {e}")
        return jsonify({"error": "Failed to update settings"}), 500


@app.route('/api/rate-image', methods=["POST"])
@jwt_required(optional=True)
def rate_image():
    """
    Rate an image using multiple beauty category prompts with OpenAI Vision model.
    ---
    tags:
      - AI
    consumes:
      - application/json
    parameters:
      - in: header
        name: Authorization
        type: string
        required: false
        description: "JWT access token. Format: Bearer <token>"
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            image_url:
              type: string
              example: "https://example.com/image.jpg"
              description: "URL of the image to rate"
            gender:
              type: string
              enum: ["male", "female", "unknown"]
              example: "male"
              description: "Gender of the camel (optional)"
    responses:
      200:
        description: Beauty ratings returned successfully
        schema:
          type: object
          properties:
            beauty_ratings:
              type: object
              properties:
                head_beauty:
                  type: object
                leg_beauty:
                  type: object
                body_beauty:
                  type: object
                neck_beauty:
                  type: object
                overall_score:
                  type: number
      400:
        description: Bad Request
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
    # TODO: Implement video processing support for beauty rating analysis
    
    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({'error': 'image_url is required'}), 400
    
    image_url = data['image_url']
    gender = data.get('gender', 'unknown')  # Default to 'unknown' if not provided
    user_id = get_jwt_identity()

    # Generate image hash for caching
    image_hash = None
    try:
        import requests
        response = requests.get(image_url)
        if response.status_code == 200:
            image_file = io.BytesIO(response.content)
            image_hash = generate_image_hash(image_file)
    except Exception as e:
        print(f"Error downloading or hashing image: {e}")
        # Continue without hash if there's an error

    # Check cache for existing results
    if image_hash:
        cached_result = BeautyResult.query.filter_by(image_hash=image_hash).first()
        if cached_result:
            print(f"Cache hit for image hash: {image_hash[:16]}...")
            
            # Check if this is a cached validation failure
            if cached_result.validation_error:
                print(f"Returning cached validation error for image hash: {image_hash[:16]}...")
                return jsonify({
                    "error": cached_result.validation_error,
                    "validation": cached_result.validation_result,
                    "cached": True,
                    "cached_at": cached_result.created_at.isoformat()
                }), 400
            
            # Return cached successful results
            return jsonify({
                "beauty_ratings": cached_result.beauty_ratings,
                "overall_score": cached_result.overall_score,
                "category_scores": cached_result.category_scores,
                "validation": cached_result.validation_result,
                "cached": True,
                "cached_at": cached_result.created_at.isoformat()
            }), 200
        else:
            print(f"Cache miss for image hash: {image_hash[:16]}...")

    # Initialize async OpenAI client for validation and analysis
    try:
        import asyncio
        from openai import AsyncOpenAI
        import json
        import time
        
        # Track processing start time
        processing_start_time = time.time()
        
        # Initialize async OpenAI client
        async_client = AsyncOpenAI(api_key=client.api_key)
        
        # Validate image contains camel before proceeding with analysis
        async def run_validation_and_analysis():
            # Step 1: Validate the image
            validation_result = await validate_camel_image(image_url, async_client)
            
            if not validation_result["success"]:
                return {
                    "error": "Image validation failed",
                    "details": validation_result["error"],
                    "validation": validation_result["validation"]
                }
            
            validation_data = validation_result["validation"]
            
            # Check if image is suitable for analysis
            if not validation_data.get("contains_camel", False):
                return {
                    "error": "No camel detected in image",
                    "validation": validation_data,
                    "feedback": validation_data.get("feedback", "The image does not contain a camel."),
                    "suggestions": [
                        "Please upload an image that clearly shows a camel",
                        "Ensure the camel is the main subject of the image",
                        "Make sure the image quality is good and not blurry"
                    ]
                }
            
            if not validation_data.get("overall_suitability", False):
                missing_parts = validation_data.get("missing_parts", [])
                quality_issues = validation_data.get("quality_issues", [])
                
                return {
                    "error": "Image not suitable for comprehensive beauty analysis",
                    "validation": validation_data,
                    "feedback": validation_data.get("feedback", "The camel in the image is not suitable for detailed analysis."),
                    "missing_parts": missing_parts,
                    "quality_issues": quality_issues,
                    "suggestions": [
                        "Upload an image where the camel's body parts are clearly visible",
                        "Ensure good lighting and image quality",
                        "The camel should be positioned to show head, neck, body, and legs"
                    ]
                }
            
            # Image passed validation, proceed with beauty analysis
            print(f"Image validation passed - proceeding with beauty analysis")
            
            # Initialize prompt loader
            prompt_loader = PromptLoader()
            available_categories = prompt_loader.get_available_categories()
            
            async def rate_beauty_category(category_name):
                """Rate a specific beauty category asynchronously using external prompts"""
                try:
                    # Get system prompt and build messages with predefined samples
                    system_prompt = prompt_loader.get_system_prompt(category_name, gender=gender if gender != 'unknown' else None)
                    messages = prompt_loader.build_messages(category_name, image_url)
                    
                    response = await async_client.chat.completions.create(
                        model="gpt-5.1",
                        messages=[
                            {"role": "system", "content": system_prompt}
                        ] + messages,
                        response_format={"type": "json_object"}
                    )
                    
                    raw_response = response.choices[0].message.content
                    try:
                        parsed_response = json.loads(raw_response)
                        
                        # Check if this is an error response from the AI
                        if isinstance(parsed_response, dict) and parsed_response.get('error') is True:
                            # Handle error response - camel not found or partially visible
                            error_message = parsed_response.get('message', 'Unknown error')
                            category = parsed_response.get('category', category_name)
                            
                            return category_name, {
                                "error": True,
                                "message": error_message,
                                "category": category,
                                "category_score": None
                            }
                        
                        return category_name, parsed_response
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        return category_name, {"score": 0, "analysis": raw_response}
                        
                except Exception as e:
                    print(f"Error rating {category_name}: {e}")
                    return category_name, {"score": 0, "analysis": f"Error: {str(e)}"}
            
            async def process_all_categories():
                """Process all beauty categories concurrently"""
                tasks = [
                    rate_beauty_category(category) 
                    for category in available_categories
                ]
                results = await asyncio.gather(*tasks)
                return dict(results)
            
            # Run async processing
            beauty_ratings = await process_all_categories()
            
            # Calculate overall score using attribute-based weighted scoring
            all_attributes = []
            
            # Collect all attributes from all categories
            for category_name, category_data in beauty_ratings.items():
                # Skip categories with errors (camel not found/partially visible)
                if isinstance(category_data, dict) and category_data.get('error') is True:
                    continue
                    
                if isinstance(category_data, dict) and 'attributes' in category_data:
                    all_attributes.extend(category_data['attributes'])
            
            # Calculate overall score using attribute-specific weights
            overall_score = calculate_weighted_score(all_attributes, gender)
            
            # Get attribute weights for response
            attribute_weights = get_all_weights()
            
            # Add category scores to each beauty rating
            for category_name, category_data in beauty_ratings.items():
                # Skip categories with errors - they already have category_score set to None
                if isinstance(category_data, dict) and category_data.get('error') is True:
                    continue
                    
                if isinstance(category_data, dict) and 'attributes' in category_data:
                    # Calculate average score for this category from its attributes
                    attribute_scores = []
                    for attr in category_data['attributes']:
                        if isinstance(attr.get('score'), (int, float)) and attr['score'] is not None:
                            attribute_scores.append(attr['score'])
                    
                    category_score = round(sum(attribute_scores) / len(attribute_scores), 2) if attribute_scores else 0
                    beauty_ratings[category_name]['category_score'] = category_score
            
            # Calculate processing time
            processing_time = time.time() - processing_start_time
            
            # Prepare category scores for caching
            category_scores = {}
            for category_name, category_data in beauty_ratings.items():
                if isinstance(category_data, dict) and 'category_score' in category_data:
                    category_scores[category_name] = category_data['category_score']
            
            # Return successful analysis results
            return {
                "success": True,
                "beauty_ratings": beauty_ratings,
                "overall_score": overall_score,
                "attribute_weights": attribute_weights,
                "categories_analyzed": available_categories,
                "processing_time": round(processing_time, 3),
                "validation": validation_data,
                "category_scores": category_scores
            }
        
        # Run the validation and analysis with proper cleanup
        async def run_with_cleanup():
            try:
                return await run_validation_and_analysis()
            finally:
                # Properly close the async client before the event loop closes
                await async_client.close()
        
        result = asyncio.run(run_with_cleanup())
        
        # Handle validation errors
        if "error" in result:
            # Cache validation failures to avoid repeated validation calls
            if image_hash:
                try:
                    validation_error = result.get("error", "Unknown validation error")
                    validation_data = result.get("validation", {})
                    
                    beauty_result = BeautyResult(
                        image_hash=image_hash,
                        image_url=image_url,
                        beauty_ratings=None,  # No beauty analysis for failed validation
                        overall_score=None,
                        category_scores=None,
                        processing_time=None,
                        validation_result=validation_data,
                        validation_error=validation_error,
                        is_valid_camel=validation_data.get("contains_camel", False)
                    )
                    db.session.add(beauty_result)
                    db.session.commit()
                    print(f"Cached validation failure for image hash: {image_hash[:16]}...")
                except Exception as cache_error:
                    print(f"Error caching validation failure: {cache_error}")
                    # Continue without caching if there's an error
            
            return jsonify(result), 400
        
        # Process successful results
        beauty_ratings = result["beauty_ratings"]
        overall_score = result["overall_score"]
        category_scores = result["category_scores"]
        processing_time = result["processing_time"]
        
        # Get attribute weights for response
        attribute_weights = get_all_weights()
        
        # Prepare final response
        final_response = {
            "beauty_ratings": beauty_ratings,
            "overall_score": overall_score,
            "attribute_weights": attribute_weights,
            "categories_analyzed": result["categories_analyzed"],
            "processing_time": processing_time,
            "validation": result["validation"]
        }
        
        # Save to cache if we have a valid image hash
        if image_hash:
            try:
                validation_data = result.get("validation", {})
                
                beauty_result = BeautyResult(
                    image_hash=image_hash,
                    image_url=image_url,
                    beauty_ratings=beauty_ratings,
                    overall_score=overall_score,
                    category_scores=category_scores,
                    processing_time=processing_time,
                    validation_result=validation_data,
                    validation_error=None,  # No error for successful analysis
                    is_valid_camel=validation_data.get("contains_camel", True)  # Assume true for successful analysis
                )
                db.session.add(beauty_result)
                db.session.commit()
                print(f"Cached results for image hash: {image_hash[:16]}...")
            except Exception as cache_error:
                print(f"Error caching results: {cache_error}")
                # Continue without caching if there's an error
        
        # Save conversation if logged in
        if user_id:
            convo = Conversation(
                user_id=user_id,
                prompt="Multi-category beauty rating analysis",
                ai_response=json.dumps(final_response),
                image_url=image_url
            )
            db.session.add(convo)
            db.session.commit()

        return jsonify(final_response), 200

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "Failed to process image"}), 500


@app.route('/api/compare-beauty', methods=["POST"])
@jwt_required(optional=True)
def compare_beauty():
    """
    Compare beauty between two camel images using multiple beauty category prompts.
    ---
    tags:
      - AI
    consumes:
      - application/json
    parameters:
      - in: header
        name: Authorization
        type: string
        required: false
        description: "JWT access token. Format: Bearer <token>"
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            image_url_1:
              type: string
              example: "https://example.com/camel1.jpg"
              description: "URL of the first camel image to compare"
            image_url_2:
              type: string
              example: "https://example.com/camel2.jpg"
              description: "URL of the second camel image to compare"
            gender:
              type: string
              enum: ["male", "female", "unknown"]
              example: "male"
              description: "Gender of the camels (optional)"
            gender:
              type: string
              enum: ["male", "female", "unknown"]
              example: "male"
              description: "Gender of the camels (optional)"
    responses:
      200:
        description: Beauty comparison returned successfully
        schema:
          type: object
          properties:
            comparison_result:
              type: object
              properties:
                camel_1:
                  type: object
                camel_2:
                  type: object
                winner:
                  type: string
                score_difference:
                  type: number
      400:
        description: Bad Request
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
    
    data = request.get_json()
    if not data or 'image_url_1' not in data or 'image_url_2' not in data:
        return jsonify({"error": "Both image URLs are required (image_url_1 and image_url_2)"}), 400

    image_url_1 = data['image_url_1']
    image_url_2 = data['image_url_2']
    gender = data.get('gender', 'unknown')  # Default to 'unknown' if not provided
    user_id = get_jwt_identity()

    # Validate gender parameter
    if gender not in ['male', 'female', 'unknown']:
        return jsonify({"error": "Gender must be 'male', 'female', or 'unknown'"}), 400

    try:
        import asyncio
        from openai import AsyncOpenAI
        import json
        import time
        
        # Track processing start time
        processing_start_time = time.time()
        
        # Initialize async OpenAI client
        async_client = AsyncOpenAI(api_key=client.api_key)
        
        async def analyze_single_camel(image_url, camel_name):
            """Analyze a single camel image and return beauty ratings"""
            # Step 1: Validate the image
            validation_result = await validate_camel_image(image_url, async_client)
            
            if not validation_result["success"]:
                return {
                    "error": f"Image validation failed for {camel_name}",
                    "details": validation_result["error"],
                    "validation": validation_result["validation"]
                }
            
            validation_data = validation_result["validation"]
            
            # Check if image is suitable for analysis
            if not validation_data.get("contains_camel", False):
                return {
                    "error": f"No camel detected in {camel_name}",
                    "validation": validation_data,
                    "feedback": validation_data.get("feedback", f"The {camel_name} does not contain a camel."),
                }
            
            if not validation_data.get("overall_suitability", False):
                return {
                    "error": f"{camel_name} not suitable for comprehensive beauty analysis",
                    "validation": validation_data,
                    "feedback": validation_data.get("feedback", f"The camel in {camel_name} is not suitable for detailed analysis."),
                }
            
            # Image passed validation, proceed with beauty analysis
            print(f"{camel_name} validation passed - proceeding with beauty analysis")
            
            # Initialize prompt loader
            prompt_loader = PromptLoader()
            available_categories = prompt_loader.get_available_categories()
            
            async def rate_beauty_category(category_name):
                """Rate a specific beauty category asynchronously using external prompts"""
                try:
                    # Get system prompt and build messages with predefined samples
                    system_prompt = prompt_loader.get_system_prompt(category_name, gender=gender if gender != 'unknown' else None)
                    messages = prompt_loader.build_messages(category_name, image_url)
                    
                    response = await async_client.chat.completions.create(
                        model="gpt-5",
                        messages=[
                            {"role": "system", "content": system_prompt}
                        ] + messages,
                        response_format={"type": "json_object"}
                    )
                    
                    raw_response = response.choices[0].message.content
                    try:
                        parsed_response = json.loads(raw_response)
                        
                        # Check if this is an error response from the AI
                        if isinstance(parsed_response, dict) and parsed_response.get('error') is True:
                            # Handle error response - camel not found or partially visible
                            error_message = parsed_response.get('message', 'Unknown error')
                            category = parsed_response.get('category', category_name)
                            
                            return category_name, {
                                "error": True,
                                "message": error_message,
                                "category": category,
                                "category_score": None
                            }
                        
                        return category_name, parsed_response
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        return category_name, {"score": 0, "analysis": raw_response}
                        
                except Exception as e:
                    print(f"Error rating {category_name} for {camel_name}: {e}")
                    return category_name, {"score": 0, "analysis": f"Error: {str(e)}"}
            
            async def process_all_categories():
                """Process all beauty categories concurrently"""
                tasks = [
                    rate_beauty_category(category) 
                    for category in available_categories
                ]
                results = await asyncio.gather(*tasks)
                return dict(results)
            
            # Run async processing
            beauty_ratings = await process_all_categories()
            
            # Calculate overall score using attribute-based weighted scoring
            all_attributes = []
            
            # Collect all attributes from all categories
            for category_name, category_data in beauty_ratings.items():
                # Skip categories with errors (camel not found/partially visible)
                if isinstance(category_data, dict) and category_data.get('error') is True:
                    continue
                    
                if isinstance(category_data, dict) and 'attributes' in category_data:
                    all_attributes.extend(category_data['attributes'])
            
            # Calculate overall score using attribute-specific weights
            overall_score = calculate_weighted_score(all_attributes, gender)
            
            # Add category scores to each beauty rating
            for category_name, category_data in beauty_ratings.items():
                # Skip categories with errors - they already have category_score set to None
                if isinstance(category_data, dict) and category_data.get('error') is True:
                    continue
                    
                if isinstance(category_data, dict) and 'attributes' in category_data:
                    # Calculate average score for this category from its attributes
                    attribute_scores = []
                    for attr in category_data['attributes']:
                        if isinstance(attr.get('score'), (int, float)) and attr['score'] is not None:
                            attribute_scores.append(attr['score'])
                    
                    category_score = round(sum(attribute_scores) / len(attribute_scores), 2) if attribute_scores else 0
                    beauty_ratings[category_name]['category_score'] = category_score
            
            # Prepare category scores
            category_scores = {}
            for category_name, category_data in beauty_ratings.items():
                if isinstance(category_data, dict) and 'category_score' in category_data:
                    category_scores[category_name] = category_data['category_score']
            
            # Return successful analysis results
            return {
                "success": True,
                "beauty_ratings": beauty_ratings,
                "overall_score": overall_score,
                "categories_analyzed": available_categories,
                "validation": validation_data,
                "category_scores": category_scores
            }
        
        # Analyze both camels concurrently
        async def run_comparison_analysis():
            camel_1_task = analyze_single_camel(image_url_1, "Camel 1")
            camel_2_task = analyze_single_camel(image_url_2, "Camel 2")
            
            camel_1_result, camel_2_result = await asyncio.gather(camel_1_task, camel_2_task)
            
            return camel_1_result, camel_2_result
        
        # Run the comparison analysis with proper cleanup
        async def run_with_cleanup():
            try:
                return await run_comparison_analysis()
            finally:
                # Properly close the async client before the event loop closes
                await async_client.close()
        
        camel_1_result, camel_2_result = asyncio.run(run_with_cleanup())
        
        # Handle validation errors for either camel
        if "error" in camel_1_result:
            return jsonify({
                "error": "Camel 1 analysis failed",
                "details": camel_1_result
            }), 400
        
        if "error" in camel_2_result:
            return jsonify({
                "error": "Camel 2 analysis failed", 
                "details": camel_2_result
            }), 400
        
        # Calculate processing time
        processing_time = time.time() - processing_start_time
        
        # Determine winner and score difference
        camel_1_score = camel_1_result["overall_score"]
        camel_2_score = camel_2_result["overall_score"]
        score_difference = abs(camel_1_score - camel_2_score)
        
        if camel_1_score > camel_2_score:
            winner = "Camel 1"
        elif camel_2_score > camel_1_score:
            winner = "Camel 2"
        else:
            winner = "Tie"
        
        # Get attribute weights for response
        attribute_weights = get_all_weights()
        
        # Prepare final response
        final_response = {
            "comparison_result": {
                "camel_1": {
                    "image_url": image_url_1,
                    "beauty_ratings": camel_1_result["beauty_ratings"],
                    "overall_score": camel_1_score,
                    "category_scores": camel_1_result["category_scores"],
                    "validation": camel_1_result["validation"]
                },
                "camel_2": {
                    "image_url": image_url_2,
                    "beauty_ratings": camel_2_result["beauty_ratings"],
                    "overall_score": camel_2_score,
                    "category_scores": camel_2_result["category_scores"],
                    "validation": camel_2_result["validation"]
                },
                "winner": winner,
                "score_difference": round(score_difference, 2),
                "gender": gender
            },
            "attribute_weights": attribute_weights,
            "categories_analyzed": camel_1_result["categories_analyzed"],
            "processing_time": round(processing_time, 3)
        }
        
        # Save conversation if logged in
        if user_id:
            convo = Conversation(
                user_id=user_id,
                prompt=f"Beauty comparison analysis (Gender: {gender})",
                ai_response=json.dumps(final_response),
                image_url=f"{image_url_1} vs {image_url_2}"
            )
            db.session.add(convo)
            db.session.commit()

        return jsonify(final_response), 200

    except Exception as e:
        print(f"OpenAI API error in comparison: {e}")
        return jsonify({"error": "Failed to process comparison"}), 500


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
