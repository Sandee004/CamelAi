from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flasgger import Swagger
from datetime import datetime, timedelta, date
import os
from flask_bcrypt import Bcrypt
import time
from dotenv import load_dotenv
import json
from flask import Blueprint
from sqlalchemy.exc import IntegrityError
import cloudinary.uploader
import random
import requests
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
import base64
import re