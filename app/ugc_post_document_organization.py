import requests
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
from typing import Optional
from .auth import get_access_token

router = APIRouter()
DOCUMENT_FOLDER = Path("documents")
DOCUMENT_FOLDER.mkdir(exist_ok=True)

# 1️⃣ Inicializar la subida del documento
@router.post("/documents/org/initialize-upload")
def initialize_document_upload(org_urn: str = Body(..., embed=True)):
    """
    Inicializa la subida de un documento para una organización
    Parámetros:
    - org_urn: URN de la organización (ej: "urn:li:organization:106774347")
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acceso no disponible")

    url = "https://api.linkedin.com/rest/documents?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "initializeUploadRequest": {
            "owner": org_urn
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()["value"]
        return {
            "upload_url": data["uploadUrl"],
            "document_urn": data["document"],
            "expires_at": data.get("uploadUrlExpiresAt"),
            "message": "Inicialización de subida exitosa"
        }
    else:
        error_detail = f"Error al inicializar upload: {response.status_code} - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)

# 2️⃣ Subir el documento binario
@router.post("/documents/org/upload")
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF a subir"),
    upload_url: str = Form(..., description="URL de upload obtenida del paso 1")
):
    """
    Sube el archivo PDF a LinkedIn usando la URL proporcionada
    """
    try:
        # Validar tipo de archivo
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

        # Guardar temporalmente el archivo
        file_path = DOCUMENT_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Configurar headers para la subida
        headers = {
            "Authorization": f"Bearer {get_access_token()}",  # Requerido para documentos
            "Content-Type": "application/octet-stream"
        }

        # Subir el archivo
        with open(file_path, "rb") as f:
            response = requests.put(upload_url, headers=headers, data=f)

        if response.status_code == 201:
            return {
                "message": "Documento subido correctamente",
                "status_code": response.status_code
            }
        else:
            error_detail = f"Error al subir documento: {response.status_code} - {response.text}"
            raise HTTPException(status_code=response.status_code, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        # Eliminar el archivo temporal
        file_path.unlink(missing_ok=True)

# 3️⃣ Publicar el post con el documento
@router.post("/documents/org/post")
def post_document(
    org_urn: str = Form(...),
    document_urn: str = Form(...),
    commentary: str = Form(...),
    title: str = Form("Documento compartido desde API"),
    visibility: str = Form("PUBLIC")
):
    """
    Publica un post en LinkedIn con el documento subido previamente
    Versión corregida para manejar respuestas no-JSON
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acceso no disponible")

    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": org_urn,
        "commentary": commentary,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": title,
                "id": document_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    # Manejo mejorado de la respuesta
    if response.status_code == 201:
        response_data = {
            "message": "Documento publicado exitosamente",
            "post_id": response.headers.get("x-restli-id", "")
        }
        
        # Intenta parsear JSON solo si hay contenido
        if response.text.strip():
            try:
                response_data["data"] = response.json()
            except ValueError:
                # Si falla el parseo JSON, guardamos el texto crudo
                response_data["raw_response"] = response.text
        
        return response_data
    else:
        error_detail = f"Error al publicar el post: {response.status_code}"
        if response.text.strip():
            error_detail += f" - {response.text}"
        raise HTTPException(status_code=response.status_code, detail=error_detail)