import os

class Settings:
    PROJECT_NAME: str = "Arkastra ML Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    MODELS_DIR: str = os.getenv(
        "MODELS_DIR", 
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))
    )
    DATASETS_DIR: str = os.getenv(
        "DATASETS_DIR", 
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets"))
    )
    REPORTS_DIR: str = os.getenv(
        "REPORTS_DIR", 
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))
    )

settings = Settings()
