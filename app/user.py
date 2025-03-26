import requests
from fastapi import APIRouter, HTTPException
from .auth import get_access_token

router = APIRouter()

@router.get("/linkedin/userinfo")
def get_user_info():
    """
    Obtiene la información del usuario autenticado.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")


    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = "https://api.linkedin.com/v2/userinfo"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        user_urn = f"urn:li:person:{user_data.get('sub')}"
        return {"user_urn": user_urn}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
