# server.py
from __future__ import annotations

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Any, Dict

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from fastapi.openapi.utils import get_openapi


# ----------------------------
# Config
# ----------------------------
DEFAULT_TOKEN_FALLBACK = "BAObao200534"  # fallback only; recommended: set env var BAZI_API_TOKEN in Render
TOKEN_ENV_NAME = "BAZI_API_TOKEN"

# Optional override:
# If you set PUBLIC_BASE_URL in Render, OpenAPI will use it (best for Custom GPT Actions).
PUBLIC_BASE_URL_ENV_NAME = "PUBLIC_BASE_URL"

# Render automatically provides this for deployed services (fallback)
RENDER_EXTERNAL_URL_ENV_NAME = "RENDER_EXTERNAL_URL"


def _expected_token() -> str:
    return (os.getenv(TOKEN_ENV_NAME, DEFAULT_TOKEN_FALLBACK) or "").strip()


def _check_auth(auth: Optional[str]) -> None:
    """
    Accept either:
      - Authorization: Bearer <token>
      - Authorization: <token>
    """
    expected = _expected_token()
    if not expected:
        raise HTTPException(
            status_code=500,
            detail=f"{TOKEN_ENV_NAME} is not set and fallback token is empty.",
        )

    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    got = auth.strip()
    if got.lower().startswith("bearer "):
        got = got.split(" ", 1)[1].strip()

    if got != expected:
        raise HTTPException(status_code=403, detail="Invalid token")


def _public_base_url() -> str:
    """
    Priority:
      1) PUBLIC_BASE_URL (you set)
      2) RENDER_EXTERNAL_URL (Render sets)
      3) localhost fallback
    """
    for k in (PUBLIC_BASE_URL_ENV_NAME, RENDER_EXTERNAL_URL_ENV_NAME):
        v = (os.getenv(k) or "").strip()
        if v:
            return v.rstrip("/")
    return "http://localhost:8000"


def _find_script_path() -> str:
    """
    Prefer bazi_true_solar_v2.py in the same folder as this server.py.
    If user renamed it, attempt a best-effort lookup.
    """
    here = Path(__file__).resolve().parent
    preferred = here / "bazi_true_solar_v2.py"
    if preferred.exists():
        return str(preferred)

    candidates = list(here.glob("bazi_true_solar*"))
    py_candidates = [p for p in candidates if p.suffix == ".py"]
    if py_candidates:
        py_candidates.sort(key=lambda p: (("v2" not in p.stem.lower()), len(p.stem)))
        return str(py_candidates[0])

    raise RuntimeError("Could not find bazi_true_solar_v2.py next to server.py")


SCRIPT_PATH = _find_script_path()


# ----------------------------
# Request/Response Models
# ----------------------------
class BaziRequest(BaseModel):
    calendar: str = Field(default="gregorian", description="gregorian or lunar")
    year: int
    month: int
    day: int
    time: str = Field(description="HH or HH:MM or HH:MM:SS (also accepts HH.MM)")

    gender: str = Field(default="male", description="male or female")

    city: Optional[str] = None
    country: Optional[str] = None
    tz: Optional[str] = Field(default=None, description="IANA timezone like Asia/Shanghai")
    lon: Optional[float] = None
    lat: Optional[float] = None
    geocode: bool = Field(
        default=False,
        description="Try online geocoding (may fail). Prefer lon/lat or built-in table.",
    )
    use_dst: bool = Field(default=False, description="Include DST in standard meridian calc (default false)")

    leap_month: bool = Field(default=False, description="For lunar calendar only (-r)")

    start: int = 1850
    end: int = 2030


class BaziResponse(BaseModel):
    input: Dict[str, Any]
    resolved: Dict[str, Any]
    parsed: Dict[str, Any]
    stdout: str
    stderr: str
    returncode: int


# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(
    title="BaZi True Solar API",
    version="1.0.0",
    description="Compute BaZi (八字) using true solar time (真太阳时) by running bazi_true_solar_v2.py and returning its full output.",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=getattr(app, "description", None),
        routes=app.routes,
    )

    schema["servers"] = [{"url": _public_base_url()}]

    # Helps Custom GPT Actions not ask “Are you sure?” before POST
    try:
        schema["paths"]["/bazi/compute"]["post"]["x-openai-isConsequential"] = False
    except Exception:
        pass

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    return {
        "ok": True,
        "message": "BaZi True Solar API is running. Use POST /bazi/compute. OpenAPI: /openapi.json",
    }


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/openapi.yaml", response_class=PlainTextResponse)
def openapi_yaml():
    """
    Convenience endpoint: returns the OpenAPI JSON as text.
    (If you really want YAML, generate it offline; GPT Actions accepts JSON too.)
    """
    return PlainTextResponse(json.dumps(app.openapi(), ensure_ascii=False, indent=2), media_type="text/plain")


def _run_v2_script(req: BaziRequest) -> Dict[str, Any]:
    cmd = [sys.executable, SCRIPT_PATH]

    cal = (req.calendar or "gregorian").strip().lower()
    if cal not in ("gregorian", "lunar"):
        raise HTTPException(status_code=422, detail="calendar must be 'gregorian' or 'lunar'")

    if cal == "gregorian":
        cmd.append("-g")
    else:
        if req.leap_month:
            cmd.append("-r")

    gender = (req.gender or "male").strip().lower()
    if gender not in ("male", "female"):
        raise HTTPException(status_code=422, detail="gender must be 'male' or 'female'")
    if gender == "female":
        cmd.append("-n")

    cmd += ["--start", str(req.start), "--end", str(req.end)]
    cmd += [str(req.year), str(req.month), str(req.day), str(req.time)]

    if req.city:
        cmd += ["--city", req.city]
    if req.country:
        cmd += ["--country", req.country]
    if req.tz:
        cmd += ["--tz", req.tz]
    if req.lon is not None:
        cmd += ["--lon", str(req.lon)]
    if req.lat is not None:
        cmd += ["--lat", str(req.lat)]
    if req.geocode:
        cmd.append("--geocode")
    if req.use_dst:
        cmd.append("--use_dst")

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Computation timed out")

    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout or "",
        "stderr": p.stderr or "",
    }


def _parse_key_bits(stdout: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}

    m1 = re.search(r"输入钟表时间:\s*(.+)", stdout)
    if m1:
        parsed["civil_clock_time_line"] = m1.group(1).strip()

    m2 = re.search(
        r"真太阳时:\s*([0-9:\-\s]+)\s*\(lon=([0-9\.\-]+),\s*src=([^,]+),\s*tz=([^)]+)\)",
        stdout,
    )
    if m2:
        parsed["true_solar_time"] = m2.group(1).strip()
        parsed["longitude"] = float(m2.group(2))
        parsed["lonlat_source"] = m2.group(3).strip()
        parsed["timezone"] = m2.group(4).strip()

    return parsed


@app.post("/bazi/compute", response_model=BaziResponse)
def compute(req: BaziRequest, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)

    result = _run_v2_script(req)

    if result["returncode"] != 0:
        detail = result["stderr"].strip() or result["stdout"].strip() or "bazi_true_solar_v2.py failed"
        raise HTTPException(status_code=400, detail=detail)

    parsed = _parse_key_bits(result["stdout"])

    resolved = {
        "script_path": SCRIPT_PATH,
        "python": sys.executable,
        "argv": result["cmd"],
        "base_url_for_openapi": _public_base_url(),
        "note": "stdout is the full original output of bazi_true_solar_v2.py (authoritative).",
    }

    return BaziResponse(
        input=req.model_dump(),
        resolved=resolved,
        parsed=parsed,
        stdout=result["stdout"],
        stderr=result["stderr"],
        returncode=result["returncode"],
    )
