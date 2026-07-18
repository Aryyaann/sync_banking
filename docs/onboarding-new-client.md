# Dar de alta un cliente nuevo

Checklist completo para conectar un nuevo negocio (personal o cliente de pago) al sistema. Sigue este orden.

## 1. Crear el registro del negocio

En Railway → Postgres → Data:

```sql
INSERT INTO businesses (id, name) VALUES (gen_random_uuid(), 'Nombre del negocio');
SELECT id FROM businesses WHERE name = 'Nombre del negocio';
```

Guarda el `id` que devuelve — es el `business_id` que se usa en todos los pasos siguientes.

## 2. Registrar la aplicación en Enable Banking

Repetir por cada banco que este cliente use (un cliente puede tener varias cuentas/bancos).

1. Entrar al Control Panel de Enable Banking.
2. **Add a new application** → Environment: **Production**.
3. Generar par de clave/certificado nuevo (no reutilizar el de otro cliente):
   ```bash
   openssl genrsa -out private_<nombre_cliente>.key 2048
   MSYS_NO_PATHCONV=1 openssl req -new -x509 -days 365 -key private_<nombre_cliente>.key -out public_<nombre_cliente>.crt -subj "/C=ES/ST=Madrid/L=Madrid/O=NombreCliente/CN=sync-<nombre_cliente>"
   ```
4. Subir el `.crt`, poner nombre de la app y redirect URL (`https://` obligatorio en producción; puede ser una URL de tu dominio aunque no exista la ruta).
5. Registrar. Guardar el `application_id`.
6. Activar en modo **Restricted Production**: "Activate by linking accounts" → el propio cliente (o quien tenga acceso a la cuenta) hace login real y autoriza. Esto queda en estado "Active / Restricted".

Ver `docs/banks.md` para particularidades de autenticación según el banco del cliente.

## 3. Ejecutar el flujo de autorización y obtener la sesión

Con la clave privada nueva:

1. Ejecutar el equivalente a `start_auth_prod.py` (con el `application_id` y `psu_type` correctos — `business` si es cuenta de empresa, `personal` si no).
2. Abrir la URL de autorización, completar el login real del banco.
3. Capturar el `code` de la URL de redirección.
4. Ejecutar el equivalente a `get_session_prod.py` con ese `code` → obtener `session_id` y el `uid` de la(s) cuenta(s).

## 4. Guardar la conexión bancaria en base de datos

```sql
INSERT INTO bank_connections
(id, business_id, bank_name, application_id, account_uid, session_id, consent_valid_until)
VALUES (
  gen_random_uuid(),
  '<business_id del paso 1>',
  '<nombre del banco, ej. Banco de Sabadell>',
  '<application_id del paso 2>',
  '<account_uid del paso 3>',
  '<session_id del paso 3>',
  now() + interval '90 days'
);
```

## 5. Configurar la clave privada como variable de entorno

En Railway, servicios `web` y `sync_banking`:
- Añadir variable `{NOMBRE_BANCO}_PRIVATE_KEY` (o adaptar `sync_engine.py` para soportar múltiples claves, una por conexión — pendiente en el roadmap de generalización multi-banco).
- Pegar el contenido completo del `.key` (incluyendo `-----BEGIN/END PRIVATE KEY-----`).

## 6. Definir las reglas de categorización iniciales

Opcional pero recomendado: si el cliente tiene un histórico (Excel manual, extracto bancario), usarlo para precargar `categorization_rules` con sus contrapartes habituales, en vez de partir de cero.

```sql
INSERT INTO categorization_rules (id, business_id, rule_type, criterio, concepto_detallado, categoria)
VALUES (gen_random_uuid(), '<business_id>', 'texto_contiene', 'NOMBRE_PROVEEDOR', 'Descripción', 'Categoría');
```

## 7. Crear el usuario de acceso a la web

```bash
python scripts/create_user.py
```
(ajustar `business_id`, `email`, `password` antes de ejecutar — ver `docs/troubleshooting.md` si el email/password sale como placeholder por no haberlo cambiado antes de ejecutar)

## 8. Frontend

Decidir según el caso:
- **Cliente comparte el mismo frontend multi-tenant**: no hace falta nada nuevo, solo darle su email/contraseña.
- **Cliente con dominio y despliegue propio**: clonar `sync-banking-frontend`, ajustar la URL de la API si aplica, desplegar en Vercel (o Netlify si es de pago, ver `docs/costs.md` sobre el límite de uso comercial de Vercel Hobby) con el dominio del cliente.

## 9. Verificación final

- [ ] `curl` a `/auth/login` con las credenciales del cliente devuelve un token.
- [ ] `/transactions` devuelve datos reales de su cuenta.
- [ ] El cron sincroniza esta conexión en la siguiente ejecución programada (verificar en los logs del servicio `sync_banking`).
- [ ] Exportar a Excel funciona y el formato se ve correcto.
- [ ] Fecha de expiración del consentimiento (`consent_valid_until`) anotada en un calendario para renovar antes de que caduque.
