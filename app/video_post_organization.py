# app/video_post_organization.py
import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
from .auth import get_access_token
import shutil

router = APIRouter()

VIDEO_FOLDER = Path("videos")  # Carpeta para videos de organizaciones
VIDEO_FOLDER.mkdir(exist_ok=True)

# 1️⃣ Inicializar subida del video (ORGANIZACIÓN)
@router.post("/linkedin/organization/initialize-video-upload")
def initialize_video_upload(
    file_size_bytes: int = Body(..., embed=True),
    organization_urn: str = Body(..., embed=True, example="urn:li:organization:123456")
):
    """
    Inicializa la subida de video para una organización
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    if not organization_urn.startswith("urn:li:organization:"):
        raise HTTPException(status_code=400, detail="URN de organización inválido")

    url = "https://api.linkedin.com/rest/videos?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "initializeUploadRequest": {
            "owner": organization_urn,  # Cambio clave: owner es la organización
            "fileSizeBytes": file_size_bytes,
            "uploadCaptions": False,
            "uploadThumbnail": False
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json().get("value")
        return {
            "uploadUrl": data["uploadInstructions"][0]["uploadUrl"],
            "videoUrn": data["video"],
            "uploadToken": data.get("uploadToken", ""),
            "organizationUrn": organization_urn  # Nuevo campo
        }
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error en LinkedIn: {response.text}"
        )

# 2️⃣ Subir video binario (ORGANIZACIÓN)
@router.post("/linkedin/organization/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    upload_url: str = Form(...)
):
    """Sube el video a LinkedIn (misma implementación que usuarios)"""
    if not upload_url:
        raise HTTPException(status_code=400, detail="Falta upload_url")

    try:
        file_path = VIDEO_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }
        
        with open(file_path, "rb") as video_file:
            response = requests.put(upload_url, headers=headers, data=video_file)

        if response.status_code in [200, 201]:
            return {
                "message": "✅ Video subido correctamente",
                "etag": response.headers.get("ETag")
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al subir: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file_path.unlink(missing_ok=True)

# 3️⃣ Finalizar subida (ORGANIZACIÓN)
@router.post("/linkedin/organization/finalize-video-upload")
def finalize_video_upload(
    video_urn: str = Form(...),
    etag: str = Form(None),
    upload_token: str = Form(None)
):
    """Finaliza la subida (igual implementación que usuarios)"""
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    url = "https://api.linkedin.com/rest/videos?action=finalizeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "finalizeUploadRequest": {
            "video": video_urn,
            "uploadToken": upload_token if upload_token else ""
        }
    }

    if etag:
        payload["finalizeUploadRequest"]["uploadedPartIds"] = [etag]

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"message": "✅ Video finalizado correctamente"}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error al finalizar: {response.text}"
        )

# 4️⃣ Publicar video (ORGANIZACIÓN)
@router.post("/linkedin/organization/post-video")
def create_video_post(
    commentary: str = Form(...),
    video_urn: str = Form(...),
    organization_urn: str = Form(...)
):
    """Publica el video en la página de la organización"""
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    if not organization_urn.startswith("urn:li:organization:"):
        raise HTTPException(status_code=400, detail="URN de organización inválido")

    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": organization_urn,  # Cambio clave: author es la organización
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": "Video de la organización",
                "id": video_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    if not response.text.strip():
        return {
            "message": "✅ Video publicado (respuesta vacía de LinkedIn)",
            "data": None
        }

    try:
        return {
            "message": "✅ Video publicado",
            "data": response.json(),
            "organizationUrn": organization_urn
        }
    except requests.exceptions.JSONDecodeError:
        return {
            "message": "✅ Video publicado (respuesta no JSON)",
            "data": response.text
        }