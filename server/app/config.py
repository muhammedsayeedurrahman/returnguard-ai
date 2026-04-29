import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
ADDRESS_HASH_PEPPER = os.getenv("ADDRESS_HASH_PEPPER", "default-pepper")
USE_MOCK_VISION = os.getenv("USE_MOCK_VISION", "true").lower() == "true"
USE_MOCK_GEMINI = os.getenv("USE_MOCK_GEMINI", "false").lower() == "true"
USE_MOCK_ADDRESS = os.getenv("USE_MOCK_ADDRESS", "true").lower() == "true"
