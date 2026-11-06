# Instrucciones para desarrollar el analizador de logs

## Objetivo y alcance

Desarrollar una aplicación de consola en Python que permita seleccionar un archivo de texto mediante su ruta o un selector visual, analizar sus eventos y mostrar un resumen claro en español. La aplicacion debe permitir que el usuario seleccione el archivo que contiene los logs, no es servicio web ni base de datos.

## Formato de entrada

Cada línea no vacía representa un evento candidato. El formato válido es:

```text
[NIVEL] YYYY-MM-DD Mensaje
```

- Los niveles admitidos son exactamente `INFO`, `WARNING` y `ERROR`, en mayúsculas y entre corchetes.
- El orden obligatorio es nivel, fecha y mensaje.
- La fecha debe tener exactamente el formato `YYYY-MM-DD` y representar una fecha real del calendario. Validar tanto su forma como su valor; por ejemplo, `2025-02-29` es inválida y `2024-02-29` es válida.
- El mensaje debe contener al menos un carácter distinto de espacios.
- Permitir espacios o tabulaciones adicionales entre campos y al principio o al final de la línea. Conservar los espacios internos del mensaje.
- Usar guiones ASCII en las fechas. Las viñetas de los ejemplos del enunciado no forman parte del archivo.
- Las líneas vacías o que solo contienen espacios se ignoran y no cuentan como eventos ni como errores.

## Validaciones y contabilización

Mantener separadas la severidad del evento y las incidencias de validación. Un evento con nivel `ERROR` no implica por sí mismo un error de formato.

Para cada línea no vacía:

1. Incrementar el total de eventos, aunque la línea sea inválida.
2. Identificar el nivel únicamente si aparece como primer campo con sus corchetes. Si es reconocido, incrementar su contador incluso si la fecha o el mensaje son inválidos. En otro caso, incrementar el contador de nivel desconocido o ausente.
3. Verificar la fecha en la posición esperada, inmediatamente después del campo de nivel. Si falta, tiene formato incorrecto o no existe en el calendario, registrar un error de fecha. No buscar fechas en el mensaje para corregir el orden.
4. Registrar un error de estructura si faltan los corchetes o el nivel, el nivel es desconocido, faltan campos, el orden es incorrecto o no hay mensaje. Una fecha presente pero inválida, con los demás campos completos y en orden, solo produce error de fecha.
5. Contar como línea mal formateada o incompleta toda línea con al menos una incidencia. Contarla una sola vez aunque tenga varios errores.

Una línea puede tener simultáneamente un error de fecha y uno de estructura. Los subtotales de incidencias pueden superar el número de líneas mal formateadas. No sumar incidencias para obtener ese número.

Si no se puede reconocer la estructura, no adivinar campos ni reordenarlos. Una fecha fuera de su posición se considera ausente en la posición requerida. En entradas ambiguas, priorizar detectar la incidencia sobre recuperar información: una línea sin fecha, como `[WARNING] Invalid password attempt`, registra error de fecha y de estructura por campo ausente.

Invariantes del resumen:

```text
total_eventos = INFO + WARNING + ERROR + nivel_desconocido_o_ausente
eventos_validos + lineas_mal_formateadas = total_eventos
```

## Arquitectura y organización

Usar arquitectura en capas combinada con los principios de Clean Architecture. Las dependencias deben apuntar hacia el dominio y los casos de uso.

Estructura sugerida:

```text
src/log_analyzer/
    __init__.py
    __main__.py
    domain/
        __init__.py
        models.py
        parser.py
    application/
        __init__.py
        analyze_logs.py
    infrastructure/
        __init__.py
        file_reader.py
    presentation/
        __init__.py
        cli.py
tests/
README.md
pyproject.toml
```

- **Dominio:** modelos de resultados e incidencias y función pura de análisis de una línea. Sin acceso a archivos, `input`, `print` ni dependencias de otras capas.
- **Aplicación:** caso de uso que recibe un iterable de líneas, usa el analizador de dominio y acumula el resumen. No debe conocer rutas, consola ni implementaciones de lectura.
- **Infraestructura:** lectura incremental del archivo y cierre mediante un administrador de contexto. Abrir como UTF-8 con soporte de BOM (`utf-8-sig`), sin sustituir silenciosamente caracteres inválidos.
- **Presentación:** recibir la ruta, invocar el caso de uso y mostrar el resultado o errores comprensibles.
- **Punto de entrada:** conectar las capas e iniciar la aplicación. Evitar lógica de negocio en este archivo.

Preferir funciones pequeñas, anotaciones de tipos, `dataclass` para resultados y biblioteca estándar. No incorporar frameworks ni abstracciones que no resuelvan una necesidad concreta.

## Flujo de ejecución

1. Aceptar una ruta como argumento de consola. Si no se proporciona, abrir un selector visual con Tkinter. Al cancelar, finalizar con código `1` sin analizar. Si Tkinter no está disponible o falla la interfaz gráfica, informar y recomendar pasar la ruta como argumento, sin traceback.
2. Validar que la entrada no esté vacía y abrir el archivo indicado. No restringir la extensión: debe ser texto decodificable como UTF-8.
3. Procesar el archivo línea por línea y acumular únicamente contadores. No usar `read()`, `readlines()` ni guardar todos los eventos o errores en memoria.
4. Mostrar el resumen al finalizar una lectura completa.
5. Si ocurre un error de lectura o decodificación, informar que el análisis no se completó y no presentar contadores parciales como resultado definitivo.

El resumen debe incluir total de eventos, cantidades de `INFO`, `WARNING` y `ERROR`, niveles desconocidos o ausentes, eventos válidos, líneas mal formateadas o incompletas, errores de fecha y errores de estructura. Explicar brevemente que los dos últimos contadores pueden solaparse.

Usar código de salida `0` para un análisis completado, incluso si contiene líneas inválidas, y `1` para errores que impidan completarlo. Manejar la cancelación por teclado o fin de entrada sin mostrar un traceback.

## Casos borde obligatorios

| Caso | Comportamiento esperado |
| --- | --- |
| Archivo vacío | Mostrar un mensaje informativo y resumen con contadores en cero. |
| Archivo con solo líneas vacías | Ignorar las líneas e informar que no hay eventos para analizar. |
| Nivel desconocido: `[DEBUGX] 2025-01-10 Test` | Contar nivel desconocido y error de estructura; la fecha es válida. |
| Fecha inválida: `[INFO] 2025-15-45 Login` | Contar `INFO`, error de fecha y una línea mal formateada. |
| Mensaje ausente: `[ERROR] 2025-01-10` | Contar `ERROR` y error de estructura por formato incompleto. |
| Fecha ausente: `[WARNING] Invalid password attempt` | Contar `WARNING`, error de fecha y error de estructura; una sola línea mal formateada. |
| Columnas fuera de orden | Marcar error de estructura; validar la fecha solo en su posición obligatoria. |
| Archivo de 2 GB | Procesar de forma incremental, con memoria proporcional al tamaño de una línea, sin cargar todo el archivo. |
| Caracteres especiales: `[INFO] 2025-01-10 Usuario José 😊` | Procesar correctamente en UTF-8. |
| Archivo inexistente | Manejar `FileNotFoundError` con un mensaje comprensible. |
| Permisos insuficientes | Manejar `PermissionError` con un mensaje comprensible. |
| Ruta de un directorio | Informar que se necesita un archivo. |
| UTF-8 inválido u otro error de lectura | Informar el problema sin traceback y finalizar sin resumen definitivo. |
| Espacios adicionales o tabulaciones | Normalizar los separadores permitidos sin alterar el mensaje interno. |
| Saltos de línea LF o CRLF y última línea sin salto final | Procesar correctamente. |

## Fuera de alcance

No admitir otros niveles, fechas con hora o zona horaria, formatos regionales, eventos multilínea, archivos comprimidos, seguimiento en tiempo real, detección automática de codificación ni corrección automática de registros. No imponer orden cronológico ni rechazar fechas futuras. No garantizar memoria constante para una única línea de tamaño arbitrario.

## Validación y entrega

- Probar el analizador y el acumulador con los casos anteriores, años bisiestos, fechas sin ceros iniciales y líneas con varias incidencias para verificar que no se cuentan dos veces.
- Probar la entrada por argumento y por selección visual, así como los errores de acceso y decodificación. Simular errores de permisos cuando el entorno no permita reproducirlos de forma fiable.
- Verificar el procesamiento incremental con un iterable o archivo generado; no es necesario almacenar un archivo de 2 GB en el repositorio.
- Documentar en `README.md` la versión de Python elegida, instalación, ejecución, formato admitido, reglas de conteo y un ejemplo de salida.
- Mantener los mensajes de consola y la documentación en español. Los identificadores de código pueden estar en inglés, con criterio uniforme.
- Antes de dar por terminada la implementación, ejecutar las pruebas e informar sus resultados y cualquier limitación pendiente.
