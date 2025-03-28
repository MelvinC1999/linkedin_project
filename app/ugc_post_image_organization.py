import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
from .auth import get_access_token

router = APIRouter()

IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 1️⃣ Inicializar subida UGC para organización
@router.post("/ugc/organization/initialize-image")
def initialize_ugc_image_upload(organization_urn: str = Form(...)):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "registerUploadRequest": {
            "owner": organization_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ],
            "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"]
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()["value"]
        return {
            "uploadUrl": data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
            "image_urn": data["asset"]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# 2️⃣ Subir imagen binaria
@router.post("/ugc/organization/upload-image")
def upload_image_to_linkedin(
    file: UploadFile = File(...),
    upload_url: str = Form(...),
    image_urn: str = Form(...)
):
    try:
        temp_path = os.path.join(IMAGE_FOLDER, file.filename)
        with open(temp_path, "wb") as buffer:
            buffer.write(file.file.read())

        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }

        with open(temp_path, "rb") as f:
            upload_response = requests.put(upload_url, headers=headers, data=f)

        if upload_response.status_code == 201:
            return {"message": "✅ Imagen subida exitosamente", "image_urn": image_urn}
        else:
            raise HTTPException(status_code=upload_response.status_code, detail=upload_response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 3️⃣ Publicar imagen como UGC
@router.post("/ugc/organization/post-image")
def post_ugc_image_as_organization(
    organization_urn: str = Form(...),
    commentary: str = Form(...),
    image_urn: str = Form(...)
):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": organization_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": commentary
                },
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "media": image_urn,
                        "title": {
                            "text": "Imagen UGC desde FastAPI"
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return {
            "message": "✅ Imagen publicada como organización con UGC",
            "post_id": response.headers.get("x-restli-id")
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)