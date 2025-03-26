import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
from .auth import get_access_token
from .user import get_user_info

router = APIRouter()

IMAGE_FOLDER = "images"  # Carpeta donde guardar imágenes

# 📌 1️⃣ **Inicializar la subida de la imagen en LinkedIn**
@router.post("/linkedin/upload-image")
def initialize_image_upload():
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    user_info = get_user_info()
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"])

    user_urn = user_info.get("user_urn")

    url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Linkedin-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {"initializeUploadRequest": {"owner": user_urn}}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json().get("value")
        return {"uploadUrl": data["uploadUrl"], "imageURN": data["image"]}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# 📌 2️⃣ **Subir la imagen a LinkedIn**
@router.post("/linkedin/upload-file")
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


# 📌 3️⃣ **Publicar la imagen en LinkedIn**
@router.post("/linkedin/post-image")
def create_image_post(
    commentary: str = Form(...), 
    image_urn: str = Form(...)
):
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No se encontró ningún token.")

    user_info = get_user_info()
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"])

    user_urn = user_info.get("user_urn")

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
                "title": "Imagen subida desde FastAPI",
                "id": image_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, json=payload, headers=headers)

    # ✅ Verificar si LinkedIn devuelve respuesta vacía
    if not response.text.strip():
        print(f"⚠️ Advertencia: LinkedIn devolvió una respuesta vacía (Status: {response.status_code})")
        raise HTTPException(status_code=response.status_code, detail="LinkedIn devolvió una respuesta vacía.")

    print(f"🔍 Respuesta de LinkedIn: {response.status_code}")
    print("🔍 Contenido de la respuesta:", response.text)

    try:
        return {"message": "✅ Imagen publicada con éxito en LinkedIn", "data": response.json()}
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=response.status_code, detail="⚠️ Error: LinkedIn no devolvió JSON válido.")