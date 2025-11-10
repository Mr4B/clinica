# app/api/routes/frontend.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# Determina il path assoluto della directory static
STATIC_DIR = Path(__file__).parent.parent.parent / "static"  # backend/app/static

# Whitelist delle pagine consentite
ALLOWED_PAGES = {
    "login",
    "signup",
    "dashboard",
    "profile",
    "dossiers",
    "pazienti",
    "utenti",
    "moduli",
}

@router.get("/")
async def root():
    """Pagina principale - redirect a dashboard o login"""
    index_path = STATIC_DIR / "index.html"
    
    if not index_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"index.html non trovato in {STATIC_DIR}"
        )
    
    return FileResponse(index_path)

@router.get("/{nome_pagina}")
async def serve_page(nome_pagina: str):
    """Serve pagine HTML dalla whitelist"""
    if nome_pagina not in ALLOWED_PAGES:
        raise HTTPException(
            status_code=404, 
            detail=f"Pagina '{nome_pagina}' non trovata"
        )
    
    file_path = STATIC_DIR / f"{nome_pagina}.html"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File {nome_pagina}.html non trovato in {STATIC_DIR}"
        )
    
    return FileResponse(file_path)
