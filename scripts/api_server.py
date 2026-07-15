from fastapi import FastAPI, Header, HTTPException
import subprocess
import os

app = FastAPI()

API_TOKEN = "DyWwx4k1dIKHW_7pjk4diIEpHxE6JcTtNjvM_JoWflw"
CARPETA_PROYECTO = r"C:\Users\AryanHareshNarwaniDa\Documents\Banking"

@app.post("/sync")
def trigger_sync(authorization: str = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="No autorizado")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        ["python", "run_daily_sync.py"],
        cwd=CARPETA_PROYECTO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    return {
        "success": result.returncode == 0,
        "salida": result.stdout[-2000:] if result.stdout else "",
        "error": result.stderr[-2000:] if result.returncode != 0 else None,
    }

@app.post("/test-sync")
def trigger_test_sync(authorization: str = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="No autorizado")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        ["python", "test_dummy_sync.py"],
        cwd=CARPETA_PROYECTO,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=60, env=env,
    )
    return {
        "success": result.returncode == 0,
        "salida": result.stdout[-2000:] if result.stdout else "",
        "error": result.stderr[-2000:] if result.returncode != 0 else None,
    }

@app.get("/status")
def status():
    return {"status": "vivo"}