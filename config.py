import os
from pathlib import Path

basedir = Path(__file__).parent

class Config:
    SECRET_KEY = 'petnest-simple-secret-key'  # Simple secret key
    
    # Database
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir}/instance/petnest.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    
    # CORS
    CORS_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

config = Config