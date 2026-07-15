# Sync Banking

Sincronizacion automatica de movimientos bancarios (Open Banking / Enable Banking)
con motor de categorizacion por reglas, multi-negocio.

## Estructura

- src/main.py - API (FastAPI), servicio "web" en Railway
- src/sync_engine.py - logica de sincronizacion con Enable Banking
- src/cron_sync.py - script ejecutado por el cron diario, servicio "sync_banking" en Railway
- scripts/ - utilidades puntuales (setup inicial, migracion, pruebas de conexion, ya no usadas en produccion)
- sql/schema.sql - esquema de la base de datos

## Variables de entorno

Ver .env.example. Configuradas como secrets en Railway, no como archivo .env en el repo.
