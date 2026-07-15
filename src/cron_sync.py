from sqlalchemy import create_engine, text
from sync_engine import sync_negocio, DATABASE_URL
import sys

sys.stdout.reconfigure(encoding="utf-8")
engine = create_engine(DATABASE_URL)


def main():
    with engine.connect() as conn:
        conexiones = conn.execute(text("""
            SELECT business_id, id as bank_connection_id
            FROM bank_connections WHERE active = true
        """)).mappings().all()

    print(f"Sincronizando {len(conexiones)} conexión(es) activa(s)...")
    for c in conexiones:
        resultado = sync_negocio(str(c["business_id"]), str(c["bank_connection_id"]))
        print(f"  Negocio {c['business_id']}: {resultado}")


if __name__ == "__main__":
    main()