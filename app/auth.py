"""Este módulo maneja la autenticación con LinkedIn usando FastAPI."""
import webbrowser
import requests
from fastapi import APIRouter, Request
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

router = APIRouter()

# Variables de entorno - Credenciales de LinkedIn
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Definir todos los scopes
SCOPES = (
    "openid "
    "profile "
    "r_ads_reporting "
    "r_liteprofile "
    "r_organization_social "
    "rw_organization_admin "
    "w_member_social "
    "r_ads "
    "r_emailaddress "
    "w_organization_social "
    "rw_ads "
    "r_basicprofile "
    "r_organization_admin "
    "email "
    "r_1st_connections_size"
)

AUTH_URL = (
    f"https://www.linkedin.com/oauth/v2/authorization?response_type=code"
    f"&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    f"&scope={SCOPES}"
)

# Archivo para persistencia
TOKEN_FILE = "token.txt"

@router.get("/login")
def login():
    """Abre la URL de autenticación en el navegador."""
    webbrowser.open(AUTH_URL)
    return {"message": "🔗 Abre el navegador para autenticarte en LinkedIn"}

@router.get("/callbackin")
def linkedin_callback(request: Request, code: str):
    """
    Captura el 'code' de LinkedIn y obtiene el access_token.
    """
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(token_url, data=payload)

    if response.status_code == 200:
        access_token = response.json().get("access_token")

        # Guardar el token en un archivo
        with open(TOKEN_FILE, "w") as file:
            file.write(access_token)

        print(f"🔑 Access Token obtenido y almacenado en {TOKEN_FILE}")
        return {"access_token": access_token}
    else:
        return {"error": response.text}

def get_access_token():
    """
    Obtiene el token desde el archivo.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    else:
        return None