import jwt as pyjwt
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import os

APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"
SESSION_ID = "PEGA_AQUI_TU_SESSION_ID"
ACCOUNT_UID = "63d97c75-9cff-476c-b4a1-23f9b2294aeb"
EXCEL_PATH = "movimientos_sabadell.xlsx"

private_key = open(PRIVATE_KEY_PATH, "rb").read()

iat = int(datetime.now().timestamp())
jwt_body = {
    "iss": "enablebanking.com",
    "aud": "api.enablebanking.com",
    "iat": iat,
    "exp": iat + 3600,
}
jwt_token = pyjwt.encode(jwt_body, private_key, algorithm="RS256", headers={"kid": APPLICATION_ID})
base_headers = {"Authorization": f"Bearer {jwt_token}"}

# 1. Cargar Excel existente (si existe y tiene el formato correcto)
if os.path.exists(EXCEL_PATH):
    df_existente = pd.read_excel(EXCEL_PATH)
    if "referencia_unica" in df_existente.columns:
        referencias_existentes = set(df_existente["referencia_unica"].astype(str))
    else:
        print("⚠️  El Excel existente tiene un formato antiguo, se regenerará desde cero.")
        df_existente = pd.DataFrame()
        referencias_existentes = set()
else:
    df_existente = pd.DataFrame()
    referencias_existentes = set()

# 2. Pedir movimientos de los últimos 89 días (por si acaso hay retraso en el banco)
r = requests.get(
    f"https://api.enablebanking.com/accounts/{ACCOUNT_UID}/transactions",
    headers=base_headers,
    params={
        "date_from": (date.today() - timedelta(days=89)).isoformat(),
        "date_to": date.today().isoformat(),
    },
)

if r.status_code == 401 or r.status_code == 403:
    print("⚠️  La sesión ha expirado. Hay que rehacer el login (start_auth_prod.py) y actualizar SESSION_ID.")
    exit()
elif r.status_code != 200:
    print(f"Error {r.status_code}:", r.text)
    exit()

data = r.json()
transactions = data.get("transactions", [])

# 3. Filtrar solo las que NO tenemos ya
nuevas = []
for t in transactions:
    ref_unica = f"{t.get('entry_reference')}_{t.get('booking_date')}_{t['transaction_amount']['amount']}"
    if ref_unica not in referencias_existentes:
        nuevas.append({
            "referencia_unica": ref_unica,
            "fecha": t.get("booking_date"),
            "importe": t["transaction_amount"]["amount"],
            "moneda": t["transaction_amount"]["currency"],
            "tipo": "Entrada" if t.get("credit_debit_indicator") == "CRDT" else "Salida",
            "contraparte": (t.get("creditor") or {}).get("name") or (t.get("debtor") or {}).get("name"),
            "iban_contraparte": ((t.get("creditor_account") or {}).get("iban")
                                  or (t.get("debtor_account") or {}).get("iban")),
            "concepto_banco": " | ".join(t.get("remittance_information") or []),
            "concepto_detallado": "",  # aquí irá el motor de enriquecimiento, de momento vacío
            "referencia": t.get("reference_number"),
        })

print(f"Movimientos totales en el banco (últimos 89 días): {len(transactions)}")
print(f"Movimientos nuevos a añadir: {len(nuevas)}")

# 4. Añadir solo los nuevos y guardar
if nuevas:
    df_nuevas = pd.DataFrame(nuevas)
    df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
    df_final.to_excel(EXCEL_PATH, index=False)
    print(f"✅ Excel actualizado: {EXCEL_PATH}")
else:
    print("Nada nuevo, el Excel ya está al día.")