import requests
from fastapi import APIRouter, HTTPException, Form
from .auth import get_access_token
from .user import get_user_info

router = APIRouter()

@router.post("/ugc-post/text/user")
def create_ugc_post_text_user(commentary: str = Form(...)):
    """
    Publica un post de texto en LinkedIn como USUARIO autenticado usando UGC POST.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")
    
    # Obtener el user_urn dinámicamente
    user_info = get_user_info()
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"])

    user_urn = user_info.get("user_urn") # Reemplaza con tu URN de usuario
    if not user_urn:
        raise HTTPException(status_code=400, detail="No se pudo obtener el user_urn del usuario.")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Connection": "Keep-Alive",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": user_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": commentary
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = {"error": "Respuesta vacía o no JSON desde LinkedIn"}

    if response.status_code == 201:
        return {"message": "✅ Publicado con éxito", "data": response_json}
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    else:
        raise HTTPException(status_code=response.status_code, detail=response_json)