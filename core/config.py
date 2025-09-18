import os
from dotenv import load_dotenv
import cloudinary
from openai import OpenAI

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://localhost:3000",
        "https://localhost:3001"
    ]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = [
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods"
    ]


    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("USERNAME_FOR_EMAIL")
    MAIL_PASSWORD = os.getenv("PASSWORD_FOR_EMAIL")
    MAIL_DEFAULT_SENDER = os.getenv("USERNAME_FOR_EMAIL")

    # Unifonic SMS Configuration
    UNIFONIC_APP_SID = "s9XHrhUdvbOsEnOOej8gfypPpcaAq1"
    UNIFONIC_SENDER_ID = "LE MURE"
    UNIFONIC_API_URL = "https://el.cloud.unifonic.com/rest/SMS/messages"

    
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)
