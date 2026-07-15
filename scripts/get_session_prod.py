import jwt as pyjwt
import requests
from datetime import datetime
from pprint import pprint

APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"

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

CODE = "a118b895-9a1e-455e-a87d-ed4e2a3c6302"

r = requests.post(
    "https://api.enablebanking.com/sessions",
    json={"code": CODE},
    headers=base_headers,
)

if r.status_code == 200:
    session = r.json()
    print("Sesión creada correctamente:")
    pprint(session)
else:
    print(f"Error {r.status_code}:", r.text)