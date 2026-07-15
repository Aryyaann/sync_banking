import jwt as pyjwt
import requests
from datetime import datetime
from pprint import pprint

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

# Canjear el code por una sesión
CODE = "76ddf0f7-b7c5-40f2-b1c8-7ea3705a7677"

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