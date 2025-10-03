
#!/usr/bin/env python3
# -------------------------------------------------------
# src/main.py
# -------------------------------------------------------
# Purpose Summary:
#   - Public-safe FastAPI demo for cfo-embed.
#   - Exposes /api/healthz and /api/embed endpoints.
#   - Returns deterministic fake vectors; no models loaded.
# Audit:
#   - All actions print ISO 8601 UTC timestamps.
#   - Fails safe with 4xx/5xx and never exposes internal details.
# -------------------------------------------------------

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import numpy as np
import hashlib
import os

def ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _vec_for_text(text: str, dim: int = 8) -> list:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big") % (2**32)
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype(float)
    print(f"[{ts()}] EMBED gen_dim={dim}")
    return v.round(6).tolist()

app = FastAPI(title="cfo-embed-demo", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class EmbedRequest(BaseModel):
    texts: list

@app.get("/api/healthz")
def healthz():
    print(f"[{ts()}] HEALTHZ ok")
    return {"status": "ok"}

@app.post("/api/embed")
def embed(req: EmbedRequest = Body(...)):
    if not isinstance(req.texts, list) or len(req.texts) == 0:
        raise HTTPException(status_code=400, detail="texts list required")
    print(f"[{ts()}] EMBED count={len(req.texts)}")
    vectors = [_vec_for_text(str(t)) for t in req.texts]
    return {"vectors": vectors, "dim": len(vectors[0]), "meta": {"engine": "cfo-embed-demo", "ts": ts()}}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("EMBED_BIND", "0.0.0.0")
    port = int(os.getenv("EMBED_PORT", "8005"))
    print(f"[{ts()}] starting cfo-embed-demo on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
