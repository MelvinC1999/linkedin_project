from fastapi import FastAPI
import uvicorn
from app.auth import router as auth_router
from app.user import router as user_router
from app.post import router as post_router
from app.image_post import router as image_router
from app.video_post import router as video_router
from app.document_post import router as document_router
from app.post_organization import router as post_organization_router
from app.image_post_organization import router as image_post_organization_router
from app.video_post_organization import router as video_post_organization_router
from app.document_post_organization import router as document_post_organization_router

app = FastAPI()

# Registrar las rutas
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(post_router)
app.include_router(image_router)
app.include_router(video_router)
app.include_router(document_router)
app.include_router(post_organization_router)
app.include_router(image_post_organization_router)
app.include_router(video_post_organization_router)
app.include_router(document_post_organization_router)

# Iniciar el servidor
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)