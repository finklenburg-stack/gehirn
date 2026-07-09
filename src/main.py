from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api import chat, documents, projects
from src.api.errors import APIError, api_error_handler
from src.storage import db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))

app = FastAPI(title="Dokumenten-QA")

app.add_exception_handler(APIError, api_error_handler)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "projects.html", {"projects": db.list_projects()})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: str):
    project = db.get_project(project_id)
    if project is None:
        return templates.TemplateResponse(
            request,
            "projects.html",
            {"projects": db.list_projects(), "error": "Projekt nicht gefunden."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "projects": db.list_projects(),
            "active_project": project,
            "documents": db.list_documents(project_id),
            "history": db.list_messages(project_id),
        },
    )
