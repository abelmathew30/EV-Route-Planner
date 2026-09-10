"""
config.py — Application Configuration
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "ev-route-planner-secret-2024")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "ev_routes.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SEED_DATA_PATH = os.path.join(BASE_DIR, "data", "seed_data.json")
