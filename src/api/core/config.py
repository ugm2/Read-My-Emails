from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Email Search API"
    base_dir: str = ".email_search"
    model_name: str = "mxbai-embed-large"
    
    model_config = {
        'env_file': '.env',
        'extra': 'allow',
        'protected_namespaces': ()
    }

# Create a single instance
settings = Settings()

def get_settings() -> Settings:
    return settings 