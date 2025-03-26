import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path
from .auth import get_access_token
from .user import get_user_info
import shutil

router = APIRouter()

DOCUMENT_FOLDER = Path("documents")  # Carpeta para almacenar documentos temporalmente
DOCUMENT_FOLDER.mkdir(exist_ok=True)  # Crear la carpeta si no existe


# 📌 1️⃣ **Inicializar la subida del documento**
@router.post("/linkedin/initialize-document-upload")
def initialize_document_upload():
    """
    Inicializa la subida de un documento en LinkedIn y devuelve el uploadUrl y el documentURN.
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

    url = "https://api.linkedin.com/rest/documents?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "initializeUploadRequest": {
            "owner": user_urn
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json().get("value")
        return {
            "uploadUrl": data["uploadUrl"],
            "documentUrn": data["document"]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# 📌 2️⃣ **Subir el documento**
@router.post("/linkedin/upload-document")
async def upload_document(file: UploadFile = File(...), upload_url: str = Form(...)):
    """
    Sube el documento a LinkedIn usando el uploadUrl.
    """
    if not upload_url:
        raise HTTPException(status_code=400, detail="Falta el upload_url.")

    try:
        # Guardar temporalmente el documento en la carpeta local
        file_path = DOCUMENT_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Subir el documento a LinkedIn
        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }
        with open(file_path, "rb") as document_file:
            response = requests.put(upload_url, headers=headers, data=document_file)

        # Verificar si la subida fue exitosa (201 Created o 200 OK)
        if response.status_code in [200, 201]:
            return {
                "message": "✅ Documento subido correctamente"
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al subir el documento: {response.status_code} - {response.text}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        # Eliminar el archivo temporal
        file_path.unlink(missing_ok=True)


# 📌 3️⃣ **Publicar el documento en LinkedIn**
@router.post("/linkedin/post-document")
def create_document_post(commentary: str = Form(...), document_urn: str = Form(...)):
    """
    Publica un documento en LinkedIn.
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
                "title": "Documento Subido desde FastAPI",
                "id": document_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return {"message": "✅ Documento publicado con éxito en LinkedIn"}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error al publicar el documento: {response.status_code} - {response.text}"
        )