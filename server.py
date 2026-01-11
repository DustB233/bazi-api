from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
import datetime, math
import pytz
import os

# pip install lunar_python
from lunar_python import Solar  # Lunar can be accessed via solar.getLunar()

app = FastAPI(
    title="BaZi True Solar API",
    version="1.0.0",
    description="Compute BaZi (八字) using true solar time (真太阳时) from user inputs."
)

# --- Offline minimal city table (extend as you like) ---
CITY_LONLAT = {
    ("qingdao", "china"): (120.3826, 36.0671),
    ("beijing", "china"): (116.4074, 39.9042),
    ("shanghai", "china"): (121.4737, 31.2304),
}

def equation_of_time_minutes(dt: datetime.datetime) -> float:
    # Spencer formula approx (minutes)
    n = dt.timetuple().tm_yday
    B = 2.0 * math.pi * (n - 81) / 364.0
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

def to_true_solar_datetime(local_dt: datetime.datetime, lon_deg: float, tz: pytz.BaseTzInfo, use_dst: bool = False) -> datetime.datetime:
    """
    TrueSolar ≈ StandardTime + 4*(lon - LSTM) + EoT  (minutes)
    """
    if local_dt.tzinfo is None:
        local_dt = tz.localize(local_dt)
    else:
        local_dt = local_dt.astimezone(tz)

    offset = local_dt.utcoffset()
    offset_hours = (offset.total_seconds() / 3600.0) if offset else 0.0
    if (not use_dst) and bool(local_dt.dst()):
        offset_hours -= 1.0

    lstm = 15.0 * offset_hours  # Local Standard Time Meridian
    eot = equation_of_time_minutes(local_dt.replace(tzinfo=None))
    tc = 4.0 * (lon_deg - lstm) + eot
    return local_dt.replace(tzinfo=None) + datetime.timedelta(minutes=tc)

def parse_time(s: str) -> tuple[int,int,int]:
    s = s.strip()
    if ":" not in s and s.count(".") == 1:
        # accept HH.MM
        s = s.replace(".", ":", 1)
    parts = s.split(":")
    if len(parts) == 1:
        h, m, sec = parts[0], "0", "0"
    elif len(parts) == 2:
        h, m, sec = parts[0], parts[1], "0"
    elif len(parts) == 3:
        h, m, sec = parts
    else:
        raise ValueError("time must be HH or HH:MM or HH:MM:SS")
    hi, mi, si = int(h), int(m), int(sec)
    if not (0 <= hi <= 23 and 0 <= mi <= 59 and 0 <= si <= 59):
        raise ValueError("invalid time range")
    return hi, mi, si

class BaziRequest(BaseModel):
    calendar: Literal["gregorian"] = "gregorian"  # keep it simple at first
    year: int
    month: int
    day: int
    time: str = Field(..., description="HH or HH:MM or HH:MM:SS (also accepts HH.MM)")
    gender: Literal["male", "female"] = "male"

    # location input: either city/country or lon/lat
    city: Optional[str] = None
    country: Optional[str] = None
    lon: Optional[float] = Field(None, description="Longitude (east positive). Preferred for accuracy.")
    lat: Optional[float] = None

    tz: Optional[str] = Field(None, description="IANA timezone like Asia/Shanghai. If omitted and country==China -> Asia/Shanghai.")
    use_dst: bool = False

class BaziResponse(BaseModel):
    input: Dict[str, Any]
    resolved: Dict[str, Any]
    times: Dict[str, str]
    bazi: Dict[str, Any]

def resolve_lon_lat(req: BaziRequest) -> tuple[float, Optional[float], str]:
    if req.lon is not None:
        return req.lon, req.lat, "user_lonlat"
    if req.city and req.country:
        key = (req.city.strip().lower(), req.country.strip().lower())
        if key in CITY_LONLAT:
            lon, lat = CITY_LONLAT[key]
            return lon, lat, "builtin_city_table"
    raise HTTPException(status_code=400, detail="Need lon (recommended) or a supported city+country in builtin table.")

def resolve_tz(req: BaziRequest) -> pytz.BaseTzInfo:
    if req.tz:
        try:
            return pytz.timezone(req.tz)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid tz: {req.tz}")
    # minimal default rule:
    if (req.country or "").strip().lower() == "china":
        return pytz.timezone("Asia/Shanghai")
    raise HTTPException(status_code=400, detail="Please provide tz (e.g., Asia/Shanghai).")

def compute_bazi_true_solar(req: BaziRequest) -> dict:
    tz = resolve_tz(req)
    lon, lat, src = resolve_lon_lat(req)

    h, m, s = parse_time(req.time)
    local_civil = datetime.datetime(req.year, req.month, req.day, h, m, s)

    true_solar = to_true_solar_datetime(local_civil, lon, tz, use_dst=req.use_dst)

    # use true solar time to build Solar -> Lunar -> EightChar
    solar_true = Solar.fromYmdHms(true_solar.year, true_solar.month, true_solar.day, true_solar.hour, true_solar.minute, true_solar.second)
    lunar = solar_true.getLunar()
    ba = lunar.getEightChar()

    # pillars
    y_gan, y_zhi = ba.getYearGan(), ba.getYearZhi()
    m_gan, m_zhi = ba.getMonthGan(), ba.getMonthZhi()
    d_gan, d_zhi = ba.getDayGan(), ba.getDayZhi()
    t_gan, t_zhi = ba.getTimeGan(), ba.getTimeZhi()

    return {
        "input": req.model_dump(),
        "resolved": {"lon": lon, "lat": lat, "lonlat_source": src, "tz": tz.zone},
        "times": {
            "civil_local": local_civil.strftime("%Y-%m-%d %H:%M:%S"),
            "true_solar": true_solar.strftime("%Y-%m-%d %H:%M:%S"),
            "solar_used": solar_true.toYmdHms() if hasattr(solar_true, "toYmdHms") else true_solar.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "bazi": {
            "pillars": {
                "year": {"gan": y_gan, "zhi": y_zhi, "gz": f"{y_gan}{y_zhi}"},
                "month": {"gan": m_gan, "zhi": m_zhi, "gz": f"{m_gan}{m_zhi}"},
                "day": {"gan": d_gan, "zhi": d_zhi, "gz": f"{d_gan}{d_zhi}"},
                "hour": {"gan": t_gan, "zhi": t_zhi, "gz": f"{t_gan}{t_zhi}"},
            },
            "day_master": d_gan,
        },
    }

def check_bearer(auth: Optional[str]) -> None:
    EXPECTED = os.getenv("BAZI_API_TOKEN")
    if not EXPECTED:
        raise HTTPException(status_code=500, detail="Server missing BAZI_API_TOKEN")

    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth.split(" ", 1)[1].strip()
    if token != EXPECTED:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.post("/bazi/compute", response_model=BaziResponse)
def compute(req: BaziRequest, authorization: Optional[str] = Header(default=None)):
    check_bearer(authorization)
    return compute_bazi_true_solar(req)
