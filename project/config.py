from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).parent.parent

class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "project" / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "project" / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 240
    # access_token_expire_minutes: int = 3

# ShokhjahonNosirov
class Settings(BaseSettings):
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()