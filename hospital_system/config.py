import os
from dotenv import load_dotenv

# Load variables from .env file and override any stale system env vars
load_dotenv(override=True)

class Config:
    # --- Security & Sessions ---
    SECRET_KEY = os.getenv("SECRET_KEY", "carepulse_dev_secret_key_2026_super_safe")

    # --- Database Configuration ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///hospital.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- SMTP Mail Configuration ---
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")