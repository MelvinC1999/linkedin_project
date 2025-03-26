import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pathlib import Path
import shutil
from .auth import get_access_token

router = APIRouter()

DOCUMENT_FOLDER = Path("documents_organization")
DOCUMENT_FOLDER.mkdir(exist_ok=True)

# 📌 Paso 1: Inicializar subida para organizaciones
@router.post("/linkedin/organization/initialize-document-upload")
def initialize_document_upload_for_org(organization_urn: str = Body(..., embed=True)):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="❌ No se encontró token")

    url = "https://api.linkedin.com/rest/documents?action=initializeUpload"
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
        data = response.json()["value"]
        return {
            "uploadUrl": data["uploadUrl"],
            "documentUrn": data["document"]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# 📌 Paso 2: Subir documento a LinkedIn
@router.post("/linkedin/organization/upload-document")
async def upload_document(file: UploadFile = File(...), upload_url: str = Form(...)):
    if not upload_url:
        raise HTTPException(status_code=400, detail="Falta el upload_url")

    file_path = DOCUMENT_FOLDER / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }
        with open(file_path, "rb") as document_file:
            response = requests.put(upload_url, headers=headers, data=document_file)

        if response.status_code in [200, 201]:
            return {"message": "✅ Documento subido correctamente"}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    finally:
        file_path.unlink(missing_ok=True)

# 📌 Paso 3: Publicar documento en LinkedIn
@router.post("/linkedin/organization/post-document")
def create_document_post_for_org(
    organization_urn: str = Form(...),
    commentary: str = Form(...),
    document_urn: str = Form(...)
):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="❌ Token no encontrado")

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
                "title": "Documento desde FastAPI (organización)",
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
        raise HTTPException(status_code=response.status_code, detail=response.text)