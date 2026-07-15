from sqlalchemy import create_engine, text
import pandas as pd
import uuid

DATABASE_URL = "postgresql://postgres:MJxAMgWBOtQPpefwPUqvwgvPyaePcpnG@kodama.proxy.rlwy.net:50752/railway"

# Datos de tu conexión actual con Sabadell (los que ya tenías en run_daily_sync.py)
APPLICATION_ID = "82664702-7eca-48af-be56-fb7b69dea089"
ACCOUNT_UID = "63d97c75-9cff-476c-b4a1-23f9b2294aeb"
SESSION_ID = "PEGA_AQUI_TU_SESSION_ID"
CONSENT_VALID_UNTIL = "2026-10-09T00:00:00Z"  # ajusta a la fecha real que renovaste (90 días desde que hiciste el login)

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # 1. Crear tu negocio como primer cliente
    business_id = str(uuid.uuid4())
    conn.execute(text("""
        INSERT INTO businesses (id, name) VALUES (:id, :name)
    """), {"id": business_id, "name": "Mi empresa (prueba)"})
    print(f"✅ Negocio creado: {business_id}")

    # 2. Crear la conexión bancaria
    bank_connection_id = str(uuid.uuid4())
    conn.execute(text("""
        INSERT INTO bank_connections
        (id, business_id, bank_name, application_id, account_uid, session_id, consent_valid_until)
        VALUES (:id, :business_id, :bank_name, :app_id, :account_uid, :session_id, :consent)
    """), {
        "id": bank_connection_id,
        "business_id": business_id,
        "bank_name": "Banco de Sabadell",
        "app_id": APPLICATION_ID,
        "account_uid": ACCOUNT_UID,
        "session_id": SESSION_ID,
        "consent": CONSENT_VALID_UNTIL,
    })
    print(f"✅ Conexión bancaria creada: {bank_connection_id}")

    # 3. Migrar las reglas desde reglas_conceptos.xlsx
    reglas = pd.read_excel("reglas_conceptos.xlsx", sheet_name="reglas")
    for _, r in reglas.iterrows():
        conn.execute(text("""
            INSERT INTO categorization_rules
            (id, business_id, rule_type, criterio, concepto_detallado, categoria, notas)
            VALUES (:id, :business_id, :rule_type, :criterio, :concepto, :categoria, :notas)
        """), {
            "id": str(uuid.uuid4()),
            "business_id": business_id,
            "rule_type": r["tipo_regla"],
            "criterio": str(r["criterio"]),
            "concepto": r["concepto_detallado"],
            "categoria": r.get("categoria"),
            "notas": r.get("notas"),
        })
    print(f"✅ {len(reglas)} reglas migradas")

    # Guarda estos IDs, los necesitarás para las próximas pruebas
    print(f"\n--- GUARDA ESTO ---")
    print(f"business_id: {business_id}")
    print(f"bank_connection_id: {bank_connection_id}")