import requests
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
from .auth import get_access_token
from .user import get_user_info

router = APIRouter()
VIDEO_FOLDER = Path("videos")
VIDEO_FOLDER.mkdir(exist_ok=True)

# 1️⃣ Registrar el upload (similar al que funciona en Postman)
@router.post("/ugc/user/register-upload")
def register_video_upload():
    """
    Registra la subida de un video en LinkedIn y obtiene la URL para upload.
    Devuelve:
    - uploadUrl: URL para subir el video
    - assetUrn: URN del asset que se usará para publicar
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="❌ Token no encontrado")

    user_info = get_user_info()
    user_urn = user_info.get("user_urn")
    if not user_urn:
        raise HTTPException(status_code=400, detail="❌ URN del usuario no encontrado")

    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "registerUploadRequest": {
            "owner": user_urn,
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
            "uploadUrl": data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
            "assetUrn": data["asset"]
        }
    else:
        error_detail = f"Error al registrar upload: {response.status_code} - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)

# 2️⃣ Subir el archivo binario (video)
@router.post("/ugc/user/upload-video")
async def upload_video(
    file: UploadFile = File(..., description="Archivo de video a subir"),
    upload_url: str = Form(..., description="URL de upload obtenida del registro")
):
    """
    Sube el archivo de video a LinkedIn usando la URL proporcionada.
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
                "message": "✅ Video subido correctamente",
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

# 3️⃣ Publicar el post con video UGC
@router.post("/ugc/user/post-video")
def publish_video_post(
    commentary: str = Form(..., description="Texto del post"),
    asset_urn: str = Form(..., description="URN del asset obtenido al registrar el upload")
):
    """
    Publica un post en LinkedIn con el video subido previamente.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="❌ Token no encontrado")

    user_info = get_user_info()
    user_urn = user_info.get("user_urn")
    if not user_urn:
        raise HTTPException(status_code=400, detail="❌ URN del usuario no encontrado")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": user_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": commentary
                },
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Video subido desde la API"
                        },
                        "media": asset_urn,
                        "title": {
                            "text": "Video desde API"
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
            "message": "✅ Video publicado exitosamente",
            "postId": response.headers.get("x-restli-id", ""),
            "data": response.json()
        }
    else:
        error_detail = f"Error al publicar el post: {response.status_code} - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)