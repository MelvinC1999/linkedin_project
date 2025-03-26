import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
from .auth import get_access_token
from .user import get_user_info
import shutil

router = APIRouter()

VIDEO_FOLDER = Path("videos")  # Carpeta para almacenar videos temporalmente
VIDEO_FOLDER.mkdir(exist_ok=True)  # Crear la carpeta si no existe


# 1️⃣ **Inicializar la subida del video**
@router.post("/linkedin/initialize-video-upload")
def initialize_video_upload(file_size_bytes: int = Body(..., embed=True)):
    """
    Inicializa la subida de un video en LinkedIn y devuelve el uploadUrl y el URN del video.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    user_info = get_user_info()
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"])

    user_urn = user_info.get("user_urn")
    if not user_urn:
        raise HTTPException(status_code=400, detail="No se pudo obtener el URN del usuario.")

    url = "https://api.linkedin.com/rest/videos?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "initializeUploadRequest": {
            "owner": user_urn,
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
            "uploadToken": data.get("uploadToken", "")
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# 2️⃣ **Subir el video**
@router.post("/linkedin/upload-video")
async def upload_video(file: UploadFile = File(...), upload_url: str = Form(...)):
    """
    Sube el video a LinkedIn usando el uploadUrl.
    """
    if not upload_url:
        raise HTTPException(status_code=400, detail="Falta el upload_url.")

    try:
        # Guardar temporalmente el video en la carpeta local
        file_path = VIDEO_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Subir el video a LinkedIn
        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }
        with open(file_path, "rb") as video_file:
            response = requests.put(upload_url, headers=headers, data=video_file)

        # Verificar si la subida fue exitosa (200 OK o 201 Created)
        if response.status_code in [200, 201]:
            # Capturar el ETag de la respuesta (si está disponible)
            etag = response.headers.get("ETag")
            return {
                "message": "✅ Video subido correctamente",
                "etag": etag  # Devolver el ETag para usarlo en la finalización
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al subir el video: {response.status_code} - {response.text}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        # Eliminar el archivo temporal
        file_path.unlink(missing_ok=True)


# 3️⃣ **Finalizar la subida del video**
@router.post("/linkedin/finalize-video-upload")
def finalize_video_upload(
    video_urn: str = Form(...), 
    etag: str = Form(None), 
    upload_token: str = Form(None)
):
    """
    Finaliza la subida del video en LinkedIn.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

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

    # Añadir uploadedPartIds solo si etag está presente
    if etag:
        payload["finalizeUploadRequest"]["uploadedPartIds"] = [etag]

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"message": "✅ Subida del video finalizada correctamente"}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error al finalizar la subida: {response.status_code} - {response.text}"
        )

# 4️⃣ **Publicar el video**
@router.post("/linkedin/post-video")
def create_video_post(
    commentary: str = Form(...), 
    video_urn: str = Form(...)
):
    """
    Publica un post con un video en LinkedIn.
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    user_info = get_user_info()
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"])

    user_urn = user_info.get("user_urn")
    if not user_urn:
        raise HTTPException(status_code=400, detail="No se pudo obtener el URN del usuario.")

    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": user_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": "Video subido desde FastAPI",
                "id": video_urn  # Usa el videoUrn obtenido en el Paso 1
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    # Verificar si la respuesta está vacía
    if not response.text.strip():
        return {
            "message": "✅ Video publicado con éxito en LinkedIn",
            "data": None  # LinkedIn no devolvió datos adicionales
        }

    try:
        # Intentar parsear la respuesta como JSON
        response_data = response.json()
        return {
            "message": "✅ Video publicado con éxito en LinkedIn",
            "data": response_data
        }
    except requests.exceptions.JSONDecodeError:
        # Si no se puede parsear como JSON, devolver la respuesta en texto plano
        return {
            "message": "✅ Video publicado con éxito en LinkedIn",
            "data": response.text  # Devuelve la respuesta en texto plano
        }