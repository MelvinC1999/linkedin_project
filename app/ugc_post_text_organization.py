import requests
from fastapi import APIRouter, HTTPException, Form
from .auth import get_access_token

router = APIRouter()

@router.post("/linkedin/ugc/organization/post")
def create_ugc_post_as_organization(commentary: str = Form(...)):
    """
    Publica un post UGC de texto en nombre de una organización.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acceso no disponible.")

    # Paso 1: Obtener URN de organización (donde tienes rol ADMINISTRATOR o CONTENT_ADMIN)
    try:
        org_response = requests.get(
            "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Linkedin-Version": "202503"
            }
        )

        if org_response.status_code != 200:
            raise HTTPException(
                status_code=org_response.status_code,
                detail=f"Error al obtener organizaciones: {org_response.text}"
            )

        orgs = org_response.json().get("elements", [])
        org_urn = None

        for org in orgs:
            if org.get("role") in ["ADMINISTRATOR", "CONTENT_ADMIN"]:
                org_urn = org.get("organizationalTarget")
                break

        if not org_urn:
            raise HTTPException(status_code=403, detail="No se encontró una organización válida.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Paso 2: Crear el UGC Post
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": org_urn,
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

    if response.status_code == 201:
        return {
            "message": "✅ Post UGC publicado como organización",
            "post_id": response.headers.get("x-restli-id")
        }
    else:
        try:
            detail = response.json()
        except:
            detail = {"error": "Respuesta no JSON"}
        raise HTTPException(status_code=response.status_code, detail=detail)