
## ✅ Cómo crear o editar el `README.md` directamente en GitHub para `linkedin_project`

### 1. Ve al repositorio

Abre tu navegador y entra a:

👉 [https://github.com/MelvinC1999/linkedin_project](https://github.com/MelvinC1999/linkedin_project)

---

### 2. Selecciona la rama `main`

---

### 3. README

<details>
<summary>Contenido completo del README.md</summary>

```markdown
# 🤖 LinkedIn Project - Publicador de Contenido Automatizado

Este proyecto permite publicar contenido en LinkedIn de manera automática utilizando la API REST de LinkedIn y FastAPI como framework backend.

---

## 🛠 Tecnologías utilizadas

- Python 3.10+
- FastAPI
- HTTPX
- Python-dotenv
- Pydantic
- Uvicorn

---

## 🚀 Requisitos previos

Antes de ejecutar este proyecto, asegúrate de tener instalado:

- Python 3.10 o superior
- Git (opcional pero recomendado)
- Entorno virtual (recomendado)

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/MelvinC1999/linkedin_project.git
cd linkedin_project
```

### 2. Crear y activar entorno virtual

```bash
python -m venv env
.\env\Scripts\activate  # En Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 🔐 Configuración

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```dotenv
# Credenciales de LinkedIn
CLIENT_ID=tu_client_id
CLIENT_SECRET=tu_client_secret
REDIRECT_URI=http://localhost:8080/callbackin

# Variables opcionales si ya tienes tokens o URNs
# LINKEDIN_ACCESS_TOKEN=tu_token
# DEFAULT_USER_URN=urn:li:person:xxxxxxx
# DEFAULT_ORGANIZATION_URN=urn:li:organization:xxxxxxx
```

⚠️ **Este archivo no debe subirse al repositorio. Está protegido en el `.gitignore`.**

---

## ▶️ Ejecución del proyecto

Levanta el servidor local con:

```bash
uvicorn main:app --reload
```

Luego accede a la documentación interactiva de FastAPI en:

```
http://localhost:8080/docs
```

---

## 📬 Contacto

Desarrollado por **Melvin Cevallos**  
✉️ melvin201120111@hotmail.com

---

## ⚠️ Licencia

Este proyecto es de uso académico y personal. No representa un producto final oficial ni está asociado a LinkedIn Corporation.
```
