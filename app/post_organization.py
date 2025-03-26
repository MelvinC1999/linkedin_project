import requests
from fastapi import APIRouter, HTTPException
from .auth import get_access_token

router = APIRouter()

@router.post("/linkedin/organization/post")
def create_organization_post():
    """
    Publica un post de texto como organización
    (Mismo estilo que tu endpoint para usuarios)
    """
    # 1. Obtener token (internamente)
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token")

    # 2. Obtener organización (equivalente a get_user_info)
    try:
        # Primero obtener organizaciones disponibles
        orgs_response = requests.get(
            "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Linkedin-Version": "202503"
            }
        )
        
        if orgs_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Error al obtener organizaciones: {orgs_response.text}"
            )
        
        orgs = orgs_response.json().get("elements", [])
        org_urn = None
        
        for org in orgs:
            if org.get("role") in ["ADMINISTRATOR", "CONTENT_ADMIN"]:
                org_urn = org["organizationalTarget"]
                break
        
        if not org_urn:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos en ninguna organización"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar organización: {str(e)}"
        )

    # 3. Configurar petición (igual que en usuario)
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": org_urn,
        "commentary": "¡Publicando como organización desde nuestra API!",
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    # 4. Enviar petición
    response = requests.post(url, json=payload, headers=headers)

    # 5. Manejar respuesta (idéntico a usuario)
    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = {"error": "Respuesta no JSON"}

    if response.status_code == 201:
        return {
            "message": "✅ Post publicado como organización",
            "data": response_json,
            "post_id": response.headers.get("x-restli-id")
        }
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="Token inválido")
    elif response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes para publicar"
        )
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=response_json
        )