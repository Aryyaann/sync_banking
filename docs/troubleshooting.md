# Troubleshooting

Errores reales encontrados durante el desarrollo de este proyecto, con causa y solución. Organizado por área.

## Entorno local (Windows / PowerShell / Git Bash)

### `openssl` no reconocido en PowerShell
Windows no trae OpenSSL por defecto.
- **Solución A**: usar Git Bash (si tienes Git para Windows instalado) en vez de PowerShell — trae OpenSSL integrado.
- **Solución B**: `winget install ShiningLight.OpenSSL.Light` y reiniciar la terminal.

### Git Bash reescribe rutas que empiezan por `/`
Al generar certificados con `openssl req -subj "/C=ES/ST=..."`, Git Bash (MSYS) interpreta el `/` inicial como ruta de Windows y lo corrompe.
- **Solución**: anteponer `MSYS_NO_PATHCONV=1` al comando:
  ```bash
  MSYS_NO_PATHCONV=1 openssl req -new -x509 -days 365 -key private.key -out public.crt -subj "/C=ES/ST=Madrid/L=Madrid/O=Org/CN=nombre"
  ```

### Sintaxis Bash (`cat >> archivo << 'EOF'`) no funciona en PowerShell
PowerShell no entiende heredocs de Bash.
- **Solución**: usar here-strings de PowerShell:
  ```powershell
  @'
  contenido
  multilinea
  '@ | Set-Content archivo.txt
  ```

### `curl` en PowerShell no es curl real
En PowerShell, `curl` es un alias de `Invoke-WebRequest`, con sintaxis distinta (no acepta `-H "Header: valor"` igual que curl real).
- **Solución**: usar `curl.exe` explícitamente, o la sintaxis nativa `Invoke-WebRequest -Headers @{...}`.

### `UnicodeEncodeError` / `UnicodeDecodeError` con emojis en subprocesos de Windows
Al lanzar un script Python como subproceso (ej. desde FastAPI con `subprocess.run`), Windows usa la codificación `cp1252` por defecto en vez de UTF-8, y falla al imprimir emojis (⚠️, ✅).
- **Solución robusta**: forzar UTF-8 dentro del propio script, no depender de variables de entorno externas:
  ```python
  import sys
  sys.stdout.reconfigure(encoding="utf-8")
  sys.stderr.reconfigure(encoding="utf-8")
  ```
  Y al capturar la salida del subproceso en el proceso padre, especificar también `encoding="utf-8", errors="replace"` en `subprocess.run`.

## Git y control de versiones

### `git status` muestra "No commits yet" tras clonar
Si una carpeta parece un clon pero dice "No commits yet" y todos los archivos salen como `Untracked`, no es un clon real — probablemente se copiaron archivos a mano o se hizo `git init` en vez de `git clone`.
- **Solución**: clonar de verdad con `git clone <url>` en una carpeta nueva y mover el trabajo pendiente ahí.

### Archivos de datos sensibles subidos por accidente (`.xlsx`, `.log`)
Un `.gitignore` incompleto (solo excluyendo `.key`/`.crt`) dejó pasar archivos de datos reales.
- **Solución**: `git rm --cached archivo` para sacarlo del tracking sin borrarlo localmente, y ampliar `.gitignore` (`*.xlsx`, `*.log`, etc.) **antes** de que vuelva a pasar. Nota: si ya se subió, sigue visible en el historial de commits — para purgarlo del todo hace falta `git filter-repo` (paso más delicado, no cubierto aquí).

## Railway

### `Found web command in Procfile` ignora el "Custom Start Command"
Railway prioriza el `Procfile` sobre el campo de Settings si ambos existen — un servicio de cron puede terminar arrancando como si fuera el servidor web.
- **Solución**: eliminar el `Procfile` del repo y definir el comando de arranque explícitamente en Settings → Deploy → Custom Start Command para cada servicio.

### Cron corre indefinidamente en vez de ejecutar y terminar
Si el Custom Start Command no se aplicó (por el problema del Procfile de arriba), un servicio de cron puede quedarse corriendo como servidor web indefinidamente en vez de ejecutar una vez y parar.
- **Solución**: confirmar en los Build Logs que la sección "Deploy" muestra el comando correcto (`python cron_sync.py`, no `uvicorn ...`) antes de asumir que el cron está mal configurado.

### `NotImplementedError: Algorithm 'RS256' could not be found`
`pyjwt` necesita el paquete `cryptography` instalado para usar algoritmos RSA.
- **Solución**: añadir `cryptography` a `requirements.txt`.

### `InvalidKeyError: Could not parse the provided public key`
Dos causas posibles, ambas reales en este proyecto:
1. Se pegó el contenido de un `.crt` (certificado público) en vez de un `.key` (clave privada) en la variable de entorno — mismo formato visual (`-----BEGIN...-----`), archivo equivocado.
2. Los saltos de línea de la clave PEM se aplanaron al pegarla como variable de entorno de una sola línea.
- **Solución**: verificar que el contenido empiece por `-----BEGIN PRIVATE KEY-----` (no `CERTIFICATE`), y hacer el código tolerante a saltos de línea aplanados:
  ```python
  key_env = key_env.strip().replace("\\n", "\n").replace("\r\n", "\n")
  ```

### Import falla tras mover archivos a subcarpetas (`src/`)
Al reorganizar el repo moviendo `main.py`/`cron_sync.py` a `src/`, Railway sigue intentando ejecutar desde la raíz.
- **Solución**: actualizar el Custom Start Command en cada servicio para incluir `cd src &&` antes del comando real.

### `Error loading ASGI app. Could not import module "main"`
Uvicorn no encuentra `main.py` porque no está en el directorio desde el que arranca.
- **Solución**: mismo fix que el anterior — confirmar el `cd src &&` en el Start Command, y verificar en GitHub que el archivo realmente se subió a esa ruta.

## Enable Banking / Open Banking

### `429 - ASPSP_RATE_LIMIT_EXCEEDED` / `HUB046`
Límite regulatorio de PSD2: los bancos limitan cuántas veces al día se puede consultar un consentimiento sin que el usuario esté presente (típicamente unas pocas veces al día).
- **Solución**: no es un bug — espaciar las pruebas, y en producción sincronizar como mucho una vez al día por conexión.

### `404 - ACCOUNT_DOES_NOT_EXIST`
El identificador de cuenta usado no es el correcto — hay varios campos parecidos en la respuesta de sesión (`account_id.iban`, `identification_hash`, `uid`); solo `uid` es válido para el endpoint de transacciones.

### `422 - WRONG_TRANSACTIONS_PERIOD` / "Requested time period out of bound"
El sandbox (y algunos bancos en producción) no aceptan rangos de fechas muy amplios.
- **Solución**: acotar a un rango razonable (ej. 89 días) en vez de meses/años.

### Sandbox devuelve 0 transacciones
Algunos sandboxes de banco solo simulan el flujo técnico (autenticación, autorización, listado de cuentas) sin datos de movimientos precargados — no es un fallo del código.
- **Solución**: validar con datos reales en modo Restricted Production en cuanto el flujo técnico esté confirmado en sandbox.

## Frontend / CORS

### El navegador bloquea las llamadas del frontend a la API
Sin `CORSMiddleware` configurado, o con el origen equivocado, el navegador rechaza las peticiones desde un dominio distinto al de la API.
- **Solución de desarrollo**: `allow_origins=["*"]` mientras se prueba en local.
- **Solución de producción**: restringir a la URL real del frontend desplegado (`allow_origins=["https://tu-dominio.vercel.app"]`) en cuanto se conozca.

### `401 - CLOSED_SESSION` tras renovar el consentimiento
Al rehacer el flujo de autorización (ej. para renovar antes de que caduque, o porque la sesión se cerró), Enable Banking puede asignar un **`account_uid` nuevo**, no solo un `session_id` nuevo — son independientes.
- **Síntoma**: se actualiza `session_id` en `bank_connections` pero se sigue usando el `account_uid` antiguo → la API devuelve `CLOSED_SESSION` aunque la sesión nueva esté activa.
- **Solución**: al renovar, revisar la respuesta completa de `get_session_prod.py` — actualizar en base de datos **tanto** `session_id` como `account_uid` (campo `uid` dentro de `accounts` en la respuesta), no solo el primero.
```sql
  UPDATE bank_connections 
  SET session_id = 'NUEVO_SESSION_ID', account_uid = 'NUEVO_ACCOUNT_UID' 
  WHERE business_id = '...' AND bank_name = '...';
```
