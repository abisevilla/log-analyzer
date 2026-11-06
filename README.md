# Analizador de logs

Aplicación de consola en Python 3.11 o superior, sin dependencias externas de ejecución.

## Instalación y ejecución

Ejecutar los comandos en una terminal. Usar Python 3.11 o superior y, si se trabaja con un entorno virtual, activarlo antes. Usar el mismo intérprete de Python para instalar y ejecutar la aplicación. En sistemas donde el comando sea `python3`, sustituir `python` por `python3` en todos los ejemplos.

### 1. Instalar el proyecto: `python -m pip install -e .`

```bash
python -m pip install -e .
```

Este comando instala el proyecto en el entorno de Python seleccionado. Debe ejecutarse desde la raíz del repositorio, donde está `pyproject.toml`.

- `python` inicia el intérprete de Python del entorno actual.
- `-m pip` ejecuta el gestor de paquetes `pip` con ese mismo intérprete.
- `install` solicita instalar el proyecto.
- `-e` activa la instalación editable: la aplicación utiliza el código de esta carpeta, por lo que los cambios en sus archivos Python se reflejan en la siguiente ejecución sin reinstalar.
- `.` indica el directorio actual como origen del proyecto que se va a instalar.

La instalación permite ejecutar el paquete `log_analyzer` desde la terminal. Se realiza una vez por entorno; puede ser necesario repetirla si cambia la configuración de empaquetado o se mueve la carpeta del proyecto. Para continuar desarrollando con una instalación editable, conservar la carpeta de código original.

Durante la instalación pueden generarse metadatos en `src/log_analyzer.egg-info/`, como `PKG-INFO`, `SOURCES.txt` y `top_level.txt`. Son archivos generados por las herramientas de empaquetado y no requieren edición manual. Aunque la aplicación no tiene dependencias externas de ejecución, la instalación puede necesitar acceso a Internet para obtener herramientas de construcción como `setuptools`.

Este comando prepara la aplicación; el análisis se inicia con uno de los dos comandos siguientes, que son alternativas según cómo se quiera elegir el archivo.

### 2. Analizar una ruta indicada: `python -m log_analyzer archivo.txt`

```bash
python -m log_analyzer archivo.txt
```

Este comando ejecuta la aplicación y analiza directamente el archivo indicado.

- `python -m log_analyzer` ejecuta el punto de entrada del paquete, definido en `src/log_analyzer/__main__.py`.
- `archivo.txt` es el argumento que identifica el archivo de logs. Sustituirlo por la ruta de un archivo existente; el comando no crea ese archivo.

Una ruta relativa, como `archivo.txt`, se interpreta desde el directorio actual de la terminal. También se puede indicar una ruta absoluta. Si contiene espacios, encerrarla entre comillas:

```bash
python -m log_analyzer "registros de prueba.txt"
python -m log_analyzer "/Users/main/Documents/logs/aplicacion.txt"
```

El archivo se lee línea por línea como UTF-8 y, al terminar, se muestra en consola el total de eventos, las cantidades por severidad y las incidencias de fecha y estructura. El contenido del archivo se conserva. No se exige una extensión específica.

Este modo permite trabajar desde una terminal sin entorno gráfico y no carga Tkinter. Si el archivo no existe, no se puede leer o contiene UTF-8 inválido, se muestra un error comprensible y la aplicación finaliza con código `1`. Un análisis completo devuelve `0`, incluso si encuentra registros mal formateados.

### 3. Elegir el archivo en una ventana: `python -m log_analyzer`

```bash
python -m log_analyzer
```

Este comando ejecuta la misma aplicación sin proporcionar una ruta. Al faltar ese argumento, se abre una ventana titulada «Seleccionar archivo de logs».

1. Buscar el archivo de logs en la ventana.
2. Seleccionar un único archivo y confirmar su apertura.
3. Consultar el resumen en la terminal desde la que se inició el programa.

El análisis y sus reglas son los mismos que al indicar una ruta como argumento. La ventana sirve para elegir el archivo; los resultados aparecen en consola. Si se cancela el diálogo, se muestra «Selección cancelada» y el programa termina con código `1` sin analizar archivos.

El selector requiere Tkinter y un entorno gráfico. Según la distribución de Python, Tkinter puede necesitar instalación adicional mediante el instalador de Python o el gestor de paquetes del sistema; no se instala desde PyPI. Si no está disponible o no se puede abrir la ventana, se mostrará un error y podrá ejecutar `python -m log_analyzer ruta_del_archivo`. Con una ruta como argumento no se carga Tkinter.

## Formato y validación

```text
[INFO] 2025-01-10 User logged in
[ERROR] 2025-01-10 Failed to connect to database
[WARNING] Invalid password attempt
```

El formato válido es `[NIVEL] YYYY-MM-DD Mensaje`. Solo se admiten `INFO`, `WARNING` y `ERROR`, con corchetes y mayúsculas exactas. La fecha debe tener ceros iniciales, guiones ASCII y existir en el calendario. El mensaje es obligatorio. Se permiten espacios o tabulaciones entre campos, conservando los espacios internos del mensaje. Las líneas vacías se ignoran.

El segundo campo se considera un intento de fecha si comienza con un dígito ASCII. Si ese intento es inválido, se registra un error de fecha. Si falta o comienza con texto, se registra fecha ausente y también error de estructura. El nivel desconocido, los corchetes incorrectos, los campos ausentes y el orden incorrecto producen error de estructura. No se buscan fechas en el mensaje ni se reordenan campos.

Cada línea no vacía cuenta como evento. Su nivel reconocido se cuenta incluso si tiene errores. Una línea con varias incidencias cuenta una sola vez como mal formateada; los contadores de incidencias pueden solaparse. La severidad `ERROR` no representa por sí misma un error de validación.

Para las tres líneas del ejemplo anterior:

```text
Resumen del análisis
Total de eventos: 3
INFO: 1
WARNING: 1
ERROR: 1
Nivel desconocido o ausente: 0
Eventos válidos: 2
Líneas mal formateadas o incompletas: 1
Errores de fecha: 1
Errores de estructura: 1
Los errores de fecha y estructura pueden solaparse en una misma línea.
```

## Cómo interpretar cada elemento del resumen

Tomemos como ejemplo este resultado:

```text
Resumen del análisis
Total de eventos: 14
INFO: 4
WARNING: 2
ERROR: 2
Nivel desconocido o ausente: 6
Eventos válidos: 1
Líneas mal formateadas o incompletas: 13
Errores de fecha: 7
Errores de estructura: 10
Los errores de fecha y estructura pueden solaparse en una misma línea.
```

### Resumen del análisis

Es el título del informe generado después de leer completamente el archivo. Los contadores describen el contenido analizado; no representan errores de ejecución del programa. Si la lectura falla, la aplicación informa el problema sin presentar un resumen parcial como definitivo.

### Total de eventos: 14

Se encontraron **14 líneas no vacías**. Cada una cuenta como un evento candidato, aunque su contenido sea inválido o no parezca un registro reconocible. Las líneas vacías o que solo contienen espacios o tabulaciones se ignoran. Por eso, el archivo puede tener más de 14 líneas físicas.

### INFO: 4

Cuatro eventos comienzan con el campo exacto `[INFO]`, después de quitar los espacios iniciales permitidos. Este nivel suele indicar información sobre el funcionamiento normal, como un inicio de sesión.

El contador reconoce la etiqueta; no interpreta el significado del mensaje. Una línea como `[INFO] 2025-15-45 Login` incrementa `INFO` aunque tenga una fecha inválida. Por tanto, `INFO: 4` no significa que haya cuatro eventos válidos.

### WARNING: 2

Dos eventos comienzan con `[WARNING]`. Este nivel suele identificar una advertencia o una situación que merece atención, como un intento de acceso fallido.

También se cuenta aunque falte información. Por ejemplo, `[WARNING] Invalid password attempt` incrementa `WARNING` y, además, registra errores de fecha y estructura porque falta la fecha en su posición obligatoria.

### ERROR: 2

Dos eventos comienzan con `[ERROR]`. Este nivel suele indicar un fallo registrado por la aplicación que generó los logs, como un problema de conexión.

**La severidad `ERROR` es independiente de la validez del registro.** `[ERROR] 2025-01-10 Failed to connect` es un evento válido: contiene nivel, fecha y mensaje correctos. Incrementa `ERROR` y `Eventos válidos`, sin incrementar los errores de fecha o estructura.

### Nivel desconocido o ausente: 6

En seis eventos no se reconoció uno de los tres niveles permitidos como primer campo. Algunos ejemplos son:

- `[DEBUGX] 2025-01-10 Test`: nivel no admitido.
- `[info] 2025-01-10 Test`: mayúsculas incorrectas.
- `INFO 2025-01-10 Test`: faltan los corchetes.
- `2025-01-10 [INFO] Test`: el nivel está fuera de su posición.
- `Texto sin formato`: no hay un nivel reconocible.

Cada uno de estos eventos cuenta también como error de estructura. El programa no busca una etiqueta en otra parte de la línea para corregirla. La fecha se comprueba por separado en el segundo campo: un nivel desconocido no implica necesariamente un error de fecha.

Los cuatro grupos de nivel incluyen todos los eventos y no se superponen:

```text
INFO + WARNING + ERROR + nivel desconocido o ausente = total de eventos
4    + 2       + 2     + 6                          = 14
```

### Eventos válidos: 1

Solo una de las 14 líneas cumple todas las reglas: nivel admitido en la primera posición, fecha real con formato exacto `YYYY-MM-DD` en la segunda posición y mensaje no vacío después de la fecha.

El evento válido puede tener cualquiera de las tres severidades, incluido `ERROR`. Este contador evalúa el formato del registro, no si el evento describe una operación exitosa.

### Líneas mal formateadas o incompletas: 13

Trece líneas tienen al menos un error de fecha o de estructura. Cada línea se cuenta **una sola vez** aquí, incluso si presenta ambos problemas.

Este grupo y el de eventos válidos forman el total:

```text
Eventos válidos + líneas mal formateadas o incompletas = total de eventos
1               + 13                                 = 14
```

### Errores de fecha: 7

Siete líneas no tienen una fecha válida en el segundo campo. Se incluyen fechas ausentes, formatos incorrectos y valores imposibles del calendario. Por ejemplo:

- `[INFO] 2025-15-45 Login`: mes y día imposibles.
- `[INFO] 2025-02-29 Login`: el año 2025 no es bisiesto.
- `[INFO] 2025-1-10 Login`: falta un cero en el mes.
- `[WARNING] Invalid password attempt`: falta la fecha en la posición esperada.

La validación considera un intento de fecha al segundo campo que comienza con un dígito ASCII. Si ese intento es inválido pero el nivel y el mensaje están completos, puede haber únicamente error de fecha. Si el segundo campo falta o comienza con texto, se registra también error de estructura por fecha ausente. Una fecha encontrada dentro del mensaje no sustituye la fecha obligatoria.

El contador aumenta una vez por línea afectada, aunque la fecha tenga varios defectos simultáneos.

### Errores de estructura: 10

Diez líneas incumplen la organización obligatoria `[NIVEL] YYYY-MM-DD Mensaje`: tienen un nivel ausente o desconocido, corchetes incorrectos, campos ausentes, campos fuera de orden o un mensaje vacío.

Por ejemplo, `[ERROR] 2025-01-10` tiene fecha válida pero carece de mensaje: cuenta como error de estructura, sin error de fecha. En cambio, `[INFO] 2025-15-45 Login` conserva los campos y su orden, por lo que solo registra error de fecha.

Cada línea incrementa este contador como máximo una vez, aunque tenga varios defectos estructurales.

### Los errores de fecha y estructura pueden solaparse en una misma línea

Significa que una línea puede pertenecer a ambos grupos de errores. Por ejemplo, `[WARNING] Invalid password attempt` tiene fecha ausente y estructura incompleta: suma un error de fecha, un error de estructura y **una sola** línea mal formateada.

En este resumen hay 7 líneas con error de fecha y 10 con error de estructura, pero solo 13 líneas distintas con problemas. La diferencia permite calcular que 4 líneas tienen ambos errores:

```text
Líneas con ambos errores = 7 + 10 - 13 = 4
Solo error de fecha     = 7 - 4       = 3
Solo error de estructura = 10 - 4     = 6
Líneas con problemas    = 3 + 6 + 4   = 13
```

Por eso no se deben sumar directamente `Errores de fecha` y `Errores de estructura` para obtener la cantidad de líneas inválidas. Tampoco se suman los contadores de severidad a los de validez: son dos formas de clasificar los mismos eventos.

## Lectura y errores

Se lee incrementalmente en UTF-8 estricto, con soporte de BOM, LF y CRLF. El consumo de memoria es proporcional al tamaño de una línea; no se almacenan eventos. Un archivo vacío produce un mensaje informativo y contadores en cero.

Los errores de acceso, lectura, decodificación y cancelación muestran un mensaje comprensible sin traceback. Si la lectura falla, no se muestra un resumen parcial. Los códigos de salida son `0` para análisis completado (aunque contenga eventos inválidos), `1` para fallos o cancelación y `2` para argumentos incorrectos. `--help` muestra ayuda y devuelve `0`.

No se admiten otros niveles, fechas con hora, formatos regionales, eventos multilínea, archivos comprimidos, seguimiento en tiempo real, detección de codificación ni corrección automática. Se permiten fechas futuras y eventos sin orden cronológico.

## Arquitectura y pruebas

El dominio valida líneas y define resultados; la aplicación acumula contadores sobre un iterable; la infraestructura abre archivos; la presentación gestiona consola y errores. El punto de entrada conecta las capas. El dominio y el caso de uso no acceden al disco ni a la consola.

Después de instalar el paquete:

```bash
python -m unittest discover -s tests -v
```

Las pruebas cubren validación, contadores, lectura incremental, Unicode, consola y fallos de lectura. Los errores de permisos se simulan para que las pruebas sean independientes de los permisos del entorno. No se almacena un archivo de 2 GB para verificar el procesamiento incremental.
