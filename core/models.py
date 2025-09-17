from .extensions import db
from datetime import datetime

class TempUser(db.Model):
    __tablename__ = 'temp_users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    ai_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("conversations", lazy=True))


class BeautyResult(db.Model):
    __tablename__ = 'beauty_results'
    
    id = db.Column(db.Integer, primary_key=True)
    image_hash = db.Column(db.String(200), unique=True, nullable=False, index=True)
    image_url = db.Column(db.String(500), nullable=True)
    beauty_ratings = db.Column(db.JSON, nullable=True)  # Store the complete beauty analysis results (null for validation failures)
    overall_score = db.Column(db.Float, nullable=True)
    category_scores = db.Column(db.JSON, nullable=True)  # Store individual category scores
    processing_time = db.Column(db.Float, nullable=True)  # Time taken to process in seconds
    
    # Validation fields
    validation_result = db.Column(db.JSON, nullable=True)  # Store validation results
    validation_error = db.Column(db.String(500), nullable=True)  # Store validation error message
    is_valid_camel = db.Column(db.Boolean, nullable=True)  # Quick lookup for camel validation status
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BeautyResult {self.id}: {self.image_hash[:16]}...>'
