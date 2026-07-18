# Sync Banking

Sincronización automática de movimientos bancarios vía Open Banking (PSD2), con categorización inteligente y panel web en tiempo real — para uso personal o como servicio multi-cliente.

Elimina el trabajo manual de anotar en Excel de dónde viene y a dónde va cada movimiento bancario. Conecta la cuenta una vez, define reglas de categorización, y el sistema se sincroniza solo cada día.

---

## Qué hace

- Se conecta a bancos españoles vía Open Banking (Enable Banking / PSD2), sin scraping ni credenciales bancarias almacenadas.
- Trae los movimientos automáticamente cada día mediante un cron en la nube.
- Aplica un motor de reglas (por IBAN, por IBAN+importe, o por texto en el concepto) para rellenar un "concepto detallado" y una categoría — el trabajo que antes se hacía a mano.
- Lo que ninguna regla cubre se marca para revisión, o se categoriza automáticamente mediante IA (ver `docs/ai-categorization.md`).
- Panel web con login real por usuario, tabla de movimientos en vivo, filtros por categoría, y exportación a Excel con formato profesional (colores, hojas por categoría, totales).
- Arquitectura multi-negocio desde el diseño de base de datos: cada cliente tiene sus propias cuentas, reglas y usuarios, completamente aislados.

## Bancos soportados

Cualquier banco disponible en Enable Banking. Validado end-to-end: **Banco Sabadell**. Soportados por la plataforma pero pendientes de validación propia: CaixaBank, BBVA, Banco Santander, Bankinter, Kutxabank, Unicaja Banco. Ver `docs/banks.md` para las particularidades de autenticación de cada uno.

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   API (FastAPI)  │────▶│   PostgreSQL    │
│   React (Vercel)│     │   Railway        │     │   Railway       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                  ▲
                                  │
                         ┌──────────────────┐
                         │   Cron diario    │
                         │   Railway        │
                         └──────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Enable Banking   │
                         │  (PSD2 / AISP)    │
                         └──────────────────┘
                                  │
                                  ▼
                            Banco del cliente
```

## Stack técnico

- **Backend**: Python, FastAPI, SQLAlchemy
- **Base de datos**: PostgreSQL (Railway)
- **Autenticación**: JWT propio (bcrypt + PyJWT), no depende de terceros
- **Open Banking**: Enable Banking API (JWT firmado con clave RSA, PSD2/AISP)
- **Frontend**: React + TypeScript, Vite
- **Hosting backend**: Railway (API + Postgres + cron)
- **Hosting frontend**: Vercel
- **Categorización IA (fallback)**: Claude Haiku (Anthropic)

## Estructura del repositorio

```
src/
  main.py           API — endpoints, auth, export a Excel
  auth.py           Login, hash de contraseñas, JWT
  sync_engine.py    Lógica de sincronización con Enable Banking + motor de reglas
  cron_sync.py      Entry point del cron (sincroniza todos los negocios activos)
scripts/
  ...               Utilidades puntuales: alta de negocio, alta de usuario, pruebas de conexión
sql/
  schema.sql        Esquema completo de la base de datos
docs/
  onboarding-new-client.md   Checklist paso a paso para dar de alta un cliente nuevo
  banks.md                   Particularidades de autenticación por banco
  troubleshooting.md         Errores conocidos y su solución
  costs.md                   Desglose de costes real y por cliente
  architecture.md            Decisiones de diseño y por qué
  ai-categorization.md       Cómo funciona el fallback de IA
```

## Variables de entorno

Ver `.env.example`. En producción se configuran como secrets en Railway, nunca como archivo `.env` commiteado.

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Conexión a Postgres |
| `AUTH_SECRET_KEY` | Firma de los JWT de sesión de usuario |
| `SABADELL_PRIVATE_KEY` (o `{BANCO}_PRIVATE_KEY`) | Clave privada RSA para firmar peticiones a Enable Banking, una por aplicación registrada |
| `ANTHROPIC_API_KEY` | Fallback de categorización por IA |

## Puesta en marcha local

```bash
git clone https://github.com/Aryyaann/sync-banking.git
cd sync-banking
pip install -r requirements.txt
```

Ejecuta el esquema (`sql/schema.sql`) contra tu instancia de Postgres, configura las variables de entorno, y:

```bash
cd src
uvicorn main:app --reload
```

## Despliegue

- **API + Cron**: Railway, dos servicios sobre el mismo repo (`web` con `uvicorn`, `sync_banking` con `python cron_sync.py` y Cron Schedule activado). Custom Start Command necesario en ambos — no usar `Procfile` (ver `docs/troubleshooting.md`).
- **Frontend**: Vercel, detecta Vite automáticamente. **Importante**: el plan Hobby de Vercel prohíbe uso comercial — para clientes de pago, usar Vercel Pro u otro hosting que sí lo permita (ver `docs/costs.md`).

## Dar de alta un cliente nuevo

Ver `docs/onboarding-new-client.md` para el checklist completo. Resumen: nuevo registro `businesses`, nueva app en Enable Banking (producción, restringida a las cuentas del cliente), nuevo usuario con contraseña propia, y (opcionalmente) deploy independiente del frontend con su propio dominio.

## Seguridad

- Contraseñas hasheadas con bcrypt, nunca en texto plano.
- Sesión vía JWT con expiración; el `business_id` viaja dentro del token firmado, no como parámetro manipulable.
- Claves privadas de Enable Banking solo como variables de entorno, nunca en el repositorio (`.gitignore` las excluye).
- CORS restringido al dominio real del frontend en producción.
- Cada negocio solo puede leer sus propios datos (aislamiento por `business_id` a nivel de consulta SQL).

## Costes

Ver `docs/costs.md` para el desglose completo y actualizado.

## Roadmap

- [ ] Generalizar el motor de sync para cualquier banco soportado (no solo Sabadell)
- [ ] Fallback de categorización por IA para transacciones sin regla
- [ ] Flujo de autoservicio: que el propio cliente conecte su banco desde la web, sin intervención manual
- [ ] Integración opcional con Excel/OneDrive del cliente vía Microsoft Graph