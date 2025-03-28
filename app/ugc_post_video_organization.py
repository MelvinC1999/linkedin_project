import requests
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
from typing import Optional
from .auth import get_access_token

router = APIRouter()
VIDEO_FOLDER = Path("videos")
VIDEO_FOLDER.mkdir(exist_ok=True)

## 1️⃣ Registrar el upload para organización
@router.post("/ugc/org/register-upload")
def register_org_upload(org_urn: str = Body(..., embed=True)):
    """
    Registra la subida de un video para una organización en LinkedIn
    Parámetros:
    - org_urn: URN de la organización (ej: "urn:li:organization:106774347")
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acceso no disponible")

    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "registerUploadRequest": {
            "owner": org_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
            "serviceRelationships": [
                {
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }
            ],
            "supportedUploadMechanism": ["SINGLE_REQUEST_UPLOAD"]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()["value"]
        return {
            "upload_url": data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
            "asset_urn": data["asset"],
            "message": "Registro de upload exitoso"
        }
    else:
        error_detail = f"Error al registrar upload: {response.status_code} - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)

## 2️⃣ Subir el video binario
@router.post("/ugc/org/upload-video")
async def upload_org_video(
    file: UploadFile = File(...),
    upload_url: str = Form(...)
):
    """
    Sube el archivo de video a LinkedIn para una organización
    """
    try:
        # Guardar temporalmente el archivo
        file_path = VIDEO_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Configurar headers para la subida
        headers = {"Content-Type": "application/octet-stream"}

        # Subir el archivo
        with open(file_path, "rb") as f:
            response = requests.put(upload_url, headers=headers, data=f)

        if response.status_code in [200, 201]:
            return {
                "message": "Video subido correctamente",
                "status_code": response.status_code
            }
        else:
            error_detail = f"Error al subir video: {response.status_code} - {response.text}"
            raise HTTPException(status_code=response.status_code, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        # Eliminar el archivo temporal
        file_path.unlink(missing_ok=True)

## 3️⃣ Publicar el post para la organización
@router.post("/ugc/org/post-video")
def post_org_video(
    org_urn: str = Form(...),
    asset_urn: str = Form(...),
    commentary: str = Form(...),
    video_title: Optional[str] = Form("Título del video"),
    video_description: Optional[str] = Form("Descripción del video")
):
    """
    Publica un post con video para una organización en LinkedIn
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acceso no disponible")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": org_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": commentary
                },
                "media": [
                    {
                        "status": "READY",
                        "media": asset_urn,
                        "title": {
                            "text": video_title
                        },
                        "description": {
                            "text": video_description
                        }
                    }
                ],
                "shareMediaCategory": "VIDEO"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return {
            "message": "Video publicado exitosamente",
            "post_id": response.headers.get("x-restli-id", ""),
            "data": response.json()
        }
    else:
        error_detail = f"Error al publicar el post: {response.status_code} - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)