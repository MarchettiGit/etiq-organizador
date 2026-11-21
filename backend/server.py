import asyncio
import logging
import os
import tempfile
import time
import uuid
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pymupdf
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel
from starlette.middleware.cors import CORSMiddleware
from urllib.parse import quote

from engine.defaults import default_settings
from engine.extractor import group_labels, read_pdf
from engine.organizer import build_pdf, finalize_label, order_labels, page_order

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
MAX_UPLOAD_MB = int(os.environ["MAX_UPLOAD_MB"])
TEMP_RETENTION_HOURS = float(os.environ["TEMP_RETENTION_HOURS"])
TEMP_DIR = Path(tempfile.gettempdir()) / "organizador_etiquetas"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

INDEXES: dict[str, list[IndexModel]] = {
    "jobs": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
    ],
    "settings": [IndexModel([("key", ASCENDING)], name="key", unique=True)],
}


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logging.getLogger(__name__).error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)


app = FastAPI()
api = APIRouter(prefix="/api")


class NamedItem(BaseModel):
    name: str = Field(min_length=1)
    aliases: List[str] = []


class SizeRule(BaseModel):
    value: float
    unit: str
    sort_value: float
    sort_unit: str
    note: str = ""


class Settings(BaseModel):
    qualities: List[NamedItem]
    colors: List[NamedItem]
    brands: List[NamedItem]
    size_rules: List[SizeRule] = []


class Correction(BaseModel):
    brand: Optional[str] = None
    quality: Optional[str] = None
    color: Optional[str] = None
    size_value: Optional[float] = None
    size_unit: Optional[str] = None


def _clean_items(items):
    out, seen = [], set()
    for it in items:
        name = it.name.strip()
        if name.lower() in seen:
            raise HTTPException(400, f"Nome duplicado: {name}")
        seen.add(name.lower())
        out.append({"name": name, "aliases": [a.strip() for a in it.aliases if a.strip()]})
    return out


async def get_settings_doc() -> dict:
    doc = await db.settings.find_one({"key": "main"}, {"_id": 0})
    if not doc:
        doc = {"key": "main", **default_settings(), "updated_at": datetime.now(timezone.utc).isoformat()}
        await db.settings.update_one({"key": "main"}, {"$setOnInsert": doc}, upsert=True)
        doc = await db.settings.find_one({"key": "main"}, {"_id": 0})
    return doc


def temp_path(job_id: str) -> Path:
    return TEMP_DIR / f"{job_id}.pdf"


def cleanup_temp() -> None:
    limit = time.time() - TEMP_RETENTION_HOURS * 3600
    for f in TEMP_DIR.glob("*.pdf"):
        if f.stat().st_mtime < limit:
            f.unlink(missing_ok=True)


def summarize(labels, total_pages):
    classified = sum(1 for l in labels if l["status"] == "ok")
    review = len(labels) - classified
    identified = sum(1 for l in labels if l.get("products"))
    return {
        "total_pages": total_pages,
        "labels_count": len(labels),
        "identified": identified,
        "classified": classified,
        "review": review,
        "percent": round(100 * classified / len(labels), 1) if labels else 0,
    }


def recompute(job: dict, settings: dict) -> dict:
    for l in job["labels"]:
        finalize_label(l, settings)
    ordered = order_labels(job["labels"], settings)
    job["labels"] = sorted(job["labels"], key=lambda l: l["idx"])
    job["page_order"] = page_order(ordered)
    job.update(summarize(job["labels"], job["total_pages"]))
    return job


def public_job(job: dict) -> dict:
    job = dict(job)
    job.pop("_id", None)
    job["file_available"] = temp_path(job["id"]).exists()
    return job


SUMMARY_FIELDS = {"_id": 0, "labels": 0, "page_order": 0}


@api.get("/")
async def root():
    return {"app": "Organizador de Etiquetas"}


@api.get("/settings")
async def read_settings():
    return await get_settings_doc()


@api.put("/settings")
async def save_settings(body: Settings):
    if not body.qualities or not body.colors or not body.brands:
        raise HTTPException(400, "Mantenha pelo menos uma qualidade, uma cor e uma marca")
    doc = {
        "qualities": _clean_items(body.qualities),
        "colors": _clean_items(body.colors),
        "brands": _clean_items(body.brands),
        "size_rules": [r.model_dump() for r in body.size_rules],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.settings.update_one({"key": "main"}, {"$set": doc}, upsert=True)
    return await get_settings_doc()


@api.post("/settings/reset")
async def reset_settings():
    doc = {**default_settings(), "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.settings.update_one({"key": "main"}, {"$set": doc}, upsert=True)
    return await get_settings_doc()


def _analyze(data: bytes, settings: dict):
    pages = read_pdf(data)
    labels = group_labels(pages)
    for i, l in enumerate(labels):
        l["idx"] = i
        l["manual"] = None
    job = {"labels": labels, "total_pages": len(pages)}
    recompute(job, settings)
    out = build_pdf(data, job["page_order"])
    out_pages = pymupdf.open(stream=out, filetype="pdf").page_count
    job["integrity"] = {"original_pages": len(pages), "final_pages": out_pages, "ok": out_pages == len(pages)}
    return job


@api.post("/jobs")
async def create_job(file: UploadFile = File(...), user_name: str = Form("")):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Envie apenas arquivos PDF")
    data = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Arquivo maior que {MAX_UPLOAD_MB} MB")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "O arquivo enviado não é um PDF válido")
    settings = await get_settings_doc()
    try:
        job = await asyncio.to_thread(_analyze, data, settings)
    except Exception as exc:
        logging.getLogger(__name__).exception("analyze failed")
        raise HTTPException(422, f"Não foi possível ler o PDF: {exc}")
    job.update({
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "user_name": user_name.strip()[:60] or "Não informado",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await asyncio.to_thread(cleanup_temp)
    temp_path(job["id"]).write_bytes(data)
    await db.jobs.insert_one(dict(job))
    return public_job(job)


@api.get("/jobs")
async def list_jobs(limit: int = Query(50, ge=1, le=500)):
    jobs = await db.jobs.find({}, SUMMARY_FIELDS).sort("created_at", -1).limit(limit).to_list(limit)
    for j in jobs:
        j["file_available"] = temp_path(j["id"]).exists()
    return jobs


async def _load(job_id: str) -> dict:
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Processamento não encontrado")
    return job


async def _save(job: dict):
    fields = {k: job[k] for k in ("labels", "page_order", "labels_count", "identified", "classified", "review", "percent")}
    await db.jobs.update_one({"id": job["id"]}, {"$set": fields})


@api.get("/jobs/{job_id}")
async def get_job(job_id: str):
    return public_job(await _load(job_id))


@api.put("/jobs/{job_id}/labels/{idx}")
async def correct_label(job_id: str, idx: int, body: Correction):
    job = await _load(job_id)
    if not 0 <= idx < len(job["labels"]):
        raise HTTPException(404, "Etiqueta não encontrada")
    data = body.model_dump()
    empty = not any(data[k] for k in ("brand", "quality", "color", "size_value"))
    job["labels"][idx]["manual"] = None if empty else data
    recompute(job, await get_settings_doc())
    await _save(job)
    return public_job(job)


@api.post("/jobs/{job_id}/reanalyze")
async def reanalyze(job_id: str):
    job = await _load(job_id)
    recompute(job, await get_settings_doc())
    await _save(job)
    return public_job(job)


@api.get("/jobs/{job_id}/download")
async def download(job_id: str):
    job = await _load(job_id)
    path = temp_path(job_id)
    if not path.exists():
        raise HTTPException(410, "O PDF original expirou no servidor. Envie o arquivo novamente.")
    out = await asyncio.to_thread(build_pdf, path.read_bytes(), job["page_order"])
    name = Path(job["filename"]).stem + "_organizado.pdf"
    return Response(out, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
    })


@api.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    res = await db.jobs.delete_one({"id": job_id})
    temp_path(job_id).unlink(missing_ok=True)
    if not res.deleted_count:
        raise HTTPException(404, "Processamento não encontrado")
    return {"deleted": True}


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@app.on_event("startup")
async def start_index_build():
    app.state.index_task = asyncio.create_task(ensure_indexes())


@app.on_event("shutdown")
async def shutdown_db_client():
    app.state.index_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.index_task
    client.close()
