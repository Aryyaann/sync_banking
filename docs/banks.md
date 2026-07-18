# Bancos soportados — particularidades de autenticación

Todos los bancos listados aquí se conectan a través de la misma integración con Enable Banking — solo cambia el valor de `aspsp.name` (y `aspsp.country`, siempre `"ES"`) en la petición de autorización. El código de sincronización (`sync_engine.py`) no cambia entre bancos.

Estado de validación en este proyecto: **✅ validado end-to-end** = probado con cuenta real, autorización completa y transacciones reales recibidas. **⏳ soportado, no validado** = confirmado en la documentación de Enable Banking pero no probado aún en este proyecto.

## Banco Sabadell — ✅ validado end-to-end

- `aspsp.name`: `"Banco de Sabadell"`
- Flujo: redirección estándar (`REDIRECT`), soporta `psu_type` `personal` y `business`.
- Sandbox: credenciales de prueba disponibles (usuario/contraseña/OTP fijos, ver respuesta del endpoint `/aspsps`).
- Particularidad detectada en pruebas propias: el sandbox del banco no trae datos de movimientos precargados — solo simula el flujo técnico (auth, autorización, listado de cuentas). Para ver transacciones reales hay que pasar a Restricted Production con una cuenta real.
- Límite de consultas: PSD2 limita el número de accesos diarios sin usuario presente — en pruebas se alcanzó el límite (429 `HUB046`) tras varias ejecuciones seguidas en poco tiempo.

## BBVA — ⏳ soportado, no validado

- `aspsp.name`: `"BBVA"`
- Flujo: redirección. Sin cambio automático a la app móvil.
- Autenticación siempre requiere usuario + contraseña, seguido de notificación push para aprobar por biometría o PIN en la app BBVA.
- **Particularidad importante**: BBVA distingue entre cuentas personales y de empresa — tras la redirección a la página de autenticación del banco, el usuario debe elegir explícitamente entre autenticación de empresa o particular antes de introducir credenciales. Tener esto en cuenta en la UX/instrucciones que se le dan al cliente al conectar su cuenta.
- Hay credenciales de sandbox documentadas por Enable Banking para pruebas.

## CaixaBank — ⏳ soportado, no validado

- `aspsp.name`: `"CaixaBank"`
- Flujo: redirección con SCA a través de la app CaixaBankNow, con cambio automático de app en dispositivos móviles.
- Autenticación: DNI/NIE + contraseña, seguido de biometría o PIN en la app.

## Banco Santander — ⏳ soportado, no validado

- `aspsp.name`: `"Banco Santander"`
- Enable Banking aún no ha publicado el detalle específico de su flujo de autenticación (a fecha de esta documentación). Probar primero en sandbox antes de dar el banco por soportado de cara a un cliente.

## Bankinter — ⏳ soportado, no validado

- `aspsp.name`: `"Bankinter"`
- Flujo: redirección, con SCA en la app Bankinter Móvil.
- Particularidad: no hay cambio automático de app — el usuario debe introducir sus credenciales en la página web de autenticación del banco incluso si tiene la app instalada.

## Kutxabank — ⏳ soportado, no validado

- `aspsp.name`: `"Kutxabank"`
- Flujo: redirección, SCA vía app Kutxabank.
- Particularidad: sin cambio automático de app — el usuario debe navegar manualmente a la app tras recibir la notificación push.

## Unicaja Banco — ⏳ soportado, no validado

- `aspsp.name`: `"Unicaja Banco"`
- Enable Banking no ha publicado aún el detalle de particularidades de este banco.

## Checklist para validar un banco nuevo

Cuando se vaya a soportar oficialmente un banco de los marcados como "⏳ soportado, no validado":

1. Probar en sandbox primero (`/aspsps?country=ES`, buscar el banco por nombre, confirmar credenciales de prueba).
2. Ejecutar el flujo completo de autorización en sandbox (equivalente a `start_auth.py` / `get_session.py`).
3. Confirmar si el sandbox de ese banco trae datos de movimientos o no (algunos no los traen, como se documentó con Sabadell).
4. Repetir el flujo en modo Restricted Production con una cuenta real propia antes de ofrecerlo a un cliente.
5. Documentar aquí cualquier particularidad de UX encontrada (elección personal/empresa, apps de terceros, límites de consentimiento distintos, etc.).
6. Actualizar el estado de "⏳ soportado, no validado" a "✅ validado end-to-end" con la fecha.
