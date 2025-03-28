import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .auth import get_access_token
from .user import get_user_info
import shutil
from pathlib import Path

router = APIRouter()

IMAGE_FOLDER = Path("images")

# 1️⃣ Inicializar la subida de imagen para UGC
@router.post("/ugc/user/init-upload-image")
def ugc_initialize_image_upload_user():
    access_token = get_access_token()
    user_info = get_user_info()
    user_urn = user_info.get("user_urn")

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
        value = response.json()["value"]
        return {
            "uploadUrl": value["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
            "imageURN": value["asset"]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# 2️⃣ Subir la imagen al uploadUrl (no olvidar agregar token)
@router.post("/ugc/user/upload-image")
def ugc_upload_image_user(file: UploadFile = File(...), upload_url: str = Form(...)):
    try:
        image_path = IMAGE_FOLDER / file.filename
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/octet-stream"
        }
        with open(image_path, "rb") as img_file:
            upload_response = requests.put(upload_url, headers=headers, data=img_file)

        if upload_response.status_code == 201:
            return {"message": "✅ Imagen subida correctamente"}
        else:
            raise HTTPException(status_code=upload_response.status_code, detail=upload_response.text)
    finally:
        image_path.unlink(missing_ok=True)


# 3️⃣ Crear el post con imagen UGC
@router.post("/ugc/user/post-image")
def ugc_post_image_user(commentary: str = Form(...), image_urn: str = Form(...)):
    access_token = get_access_token()
    user_info = get_user_info()
    user_urn = user_info.get("user_urn")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": user_urn,
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
                            "text": "Imagen subida vía UGC desde FastAPI"
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    post_response = requests.post(url, json=payload, headers=headers)

    if post_response.status_code == 201:
        return {
            "message": "✅ Imagen publicada como UGC post con éxito",
            "post_id": post_response.headers.get("x-restli-id")
        }
    else:
        raise HTTPException(status_code=post_response.status_code, detail=post_response.text)