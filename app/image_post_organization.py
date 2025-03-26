import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
from .auth import get_access_token

router = APIRouter()

IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Paso 1: Inicializar subida para organizaciones
@router.post("/linkedin/organization/upload-image")
def initialize_image_upload(organization_urn: str = Form(...)):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "initializeUploadRequest": {
            "owner": organization_urn
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json().get("value")
        return {
            "uploadUrl": data["uploadUrl"],
            "imageURN": data["image"]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# Paso 2: Subir el archivo binario al upload URL
@router.post("/linkedin/organization/upload-file")
def upload_image(
    file: UploadFile = File(...),
    upload_url: str = Form(...),
    image_urn: str = Form(...)
):
    if not upload_url or not image_urn:
        raise HTTPException(status_code=400, detail="Falta el upload_url o el image_urn")

    try:
        file_path = os.path.join(IMAGE_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }

        with open(file_path, "rb") as img:
            response = requests.put(upload_url, headers=headers, data=img)

        if response.status_code == 201:
            return {"message": "✅ Imagen subida correctamente", "image_urn": image_urn}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Paso 3: Crear la publicación con imagen
@router.post("/linkedin/organization/post-image")
def create_image_post(
    commentary: str = Form(...),
    image_urn: str = Form(...),
    organization_urn: str = Form(...)
):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": organization_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": "Imagen subida desde FastAPI",
                "id": image_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    if not response.text.strip():
        raise HTTPException(status_code=response.status_code, detail="Respuesta vacía desde LinkedIn.")

    try:
        return {
            "message": "✅ Imagen publicada con éxito en LinkedIn",
            "data": response.json()
        }
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=response.status_code, detail="⚠️ Error: LinkedIn no devolvió JSON válido.")