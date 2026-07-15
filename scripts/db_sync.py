from sqlalchemy import create_engine, text
import jwt as pyjwt
import requests
from datetime import datetime, date, timedelta
import uuid
import sys

sys.stdout.reconfigure(encoding="utf-8")

DATABASE_URL = "postgresql://postgres:MJxAMgWBOtQPpefwPUqvwgvPyaePcpnG@kodama.proxy.rlwy.net:50752/railway"
PRIVATE_KEY_PATH = "C:/Users/AryanHareshNarwaniDa/private_prod.key"
BUSINESS_ID = "160a1f57-26d2-497f-a190-1219f0da11e0"          # el que te imprimió seed_database.py
BANK_CONNECTION_ID = "bbd13e6c-bed6-40b3-bb9d-fb0d4fc72e1e"

engine = create_engine(DATABASE_URL)


def generar_jwt(application_id):
    private_key = open(PRIVATE_KEY_PATH, "rb").read()
    iat = int(datetime.now().timestamp())
    jwt_body = {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": iat, "exp": iat + 3600}
    return pyjwt.encode(jwt_body, private_key, algorithm="RS256", headers={"kid": application_id})


def sync_negocio(business_id, bank_connection_id):
    with engine.begin() as conn:
        conexion = conn.execute(text("""
            SELECT application_id, account_uid, session_id, consent_valid_until
            FROM bank_connections WHERE id = :id AND active = true
        """), {"id": bank_connection_id}).mappings().first()

        if not conexion:
            print(f"❌ No se encontró la conexión bancaria {bank_connection_id}")
            return

        dias_restantes = (conexion["consent_valid_until"] - datetime.now(conexion["consent_valid_until"].tzinfo)).days
        if dias_restantes <= 10:
            print(f"⚠️  AVISO: el consentimiento caduca en {dias_restantes} días.")

        headers = {"Authorization": f"Bearer {generar_jwt(conexion['application_id'])}"}

        r = requests.get(
            f"https://api.enablebanking.com/accounts/{conexion['account_uid']}/transactions",
            headers=headers,
            params={"date_from": (date.today() - timedelta(days=89)).isoformat(), "date_to": date.today().isoformat()},
        )

        if r.status_code == 429:
            print("⚠️  Límite de consultas diarias alcanzado. Se reintentará más tarde.")
            return
        if r.status_code != 200:
            print(f"❌ Error {r.status_code}: {r.text}")
            return

        transacciones = r.json().get("transactions", [])

        # Cargar reglas de este negocio, una sola vez
        reglas = conn.execute(text("""
            SELECT rule_type, criterio, concepto_detallado, categoria
            FROM categorization_rules WHERE business_id = :bid
        """), {"bid": business_id}).mappings().all()

        def aplicar_reglas(iban, importe, texto):
            for rg in reglas:
                if rg["rule_type"] == "iban_importe":
                    try:
                        iban_r, importe_r = rg["criterio"].split("|")
                    except ValueError:
                        continue
                    if iban == iban_r.strip() and f"{importe:.2f}" == f"{float(importe_r):.2f}":
                        return rg["concepto_detallado"], rg["categoria"]
            for rg in reglas:
                if rg["rule_type"] == "iban" and iban == rg["criterio"].strip():
                    return rg["concepto_detallado"], rg["categoria"]
            for rg in reglas:
                if rg["rule_type"] == "texto_contiene" and rg["criterio"].upper() in texto:
                    return rg["concepto_detallado"], rg["categoria"]
            return "⚠️ REVISAR", None

        nuevos = 0
        for t in transacciones:
            ref_unica = f"{t.get('entry_reference')}_{t.get('booking_date')}_{t['transaction_amount']['amount']}"
            iban = ((t.get("creditor_account") or {}).get("iban") or (t.get("debtor_account") or {}).get("iban") or "")
            importe = float(t["transaction_amount"]["amount"])
            contraparte = (t.get("creditor") or {}).get("name") or (t.get("debtor") or {}).get("name")
            concepto_banco = " | ".join(t.get("remittance_information") or [])
            texto = f"{contraparte or ''} {concepto_banco}".upper()

            concepto_detallado, categoria = aplicar_reglas(iban, importe, texto)

            result = conn.execute(text("""
                INSERT INTO transactions
                (id, business_id, bank_connection_id, referencia_unica, fecha, importe, moneda,
                 tipo, contraparte, iban_contraparte, concepto_banco, concepto_detallado, categoria, referencia)
                VALUES (:id, :bid, :bcid, :ref, :fecha, :importe, :moneda, :tipo, :contraparte,
                        :iban, :concepto_banco, :concepto_det, :categoria, :referencia)
                ON CONFLICT (business_id, referencia_unica) DO NOTHING
            """), {
                "id": str(uuid.uuid4()), "bid": business_id, "bcid": bank_connection_id,
                "ref": ref_unica, "fecha": t.get("booking_date"), "importe": importe,
                "moneda": t["transaction_amount"]["currency"],
                "tipo": "Entrada" if t.get("credit_debit_indicator") == "CRDT" else "Salida",
                "contraparte": contraparte, "iban": iban, "concepto_banco": concepto_banco,
                "concepto_det": concepto_detallado, "categoria": categoria,
                "referencia": t.get("reference_number"),
            })
            if result.rowcount > 0:
                nuevos += 1

        print(f"Movimientos del banco: {len(transacciones)} | Nuevos insertados: {nuevos}")


if __name__ == "__main__":
    sync_negocio(BUSINESS_ID, BANK_CONNECTION_ID)