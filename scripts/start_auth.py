import jwt as pyjwt
import requests
import uuid
from datetime import datetime, timezone, timedelta

APPLICATION_ID = "dab24098-2efd-40f5-b516-70bf71f96fa5"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private.key"

private_key = open(PRIVATE_KEY_PATH, "rb").read()

iat = int(datetime.now().timestamp())
jwt_body = {
    "iss": "enablebanking.com",
    "aud": "api.enablebanking.com",
    "iat": iat,
    "exp": iat + 3600,
}

jwt_token = pyjwt.encode(
    jwt_body,
    private_key,
    algorithm="RS256",
    headers={"kid": APPLICATION_ID},
)

base_headers = {"Authorization": f"Bearer {jwt_token}"}

# Lanzar la autorización contra Sabadell
body = {
    "access": {
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    },
    "aspsp": {"name": "Banco de Sabadell", "country": "ES"},
    "state": str(uuid.uuid4()),
    "redirect_url": "http://localhost:8000/callback",
    "psu_type": "business",
}

r = requests.post("https://api.enablebanking.com/auth", json=body, headers=base_headers)
if r.status_code == 200:
    auth_url = r.json()["url"]
    print(f"Abre esta URL en el navegador:\n{auth_url}")
else:
    print(f"Error {r.status_code}:", r.text)