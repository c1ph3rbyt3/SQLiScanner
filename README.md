<<<<<<< HEAD
# Escáner de SQLi (método GET)

Este repositorio contiene un **script** que busca inyecciones SQL en los **parámetros GET** de URLs. Está diseñado para detectar posibles vulnerabilidades en aplicaciones web, y cuenta con **múltiples payloads**, capacidad de **múltiples hilos**, **uso de proxies** opcional y **funciones de tamper** para obfuscar las inyecciones.

---

## Características principales

- **Inyección en parámetros GET**: Escanea cada parámetro encontrado en la URL para inyectar payloads de SQLi.
- **Detección de errores SQL** en la respuesta: Busca cadenas y patrones comunes de error en diferentes motores de bases de datos (MySQL, MSSQL, PostgreSQL, Oracle, etc.).
- **Múltiples hilos (threads)**: Permite procesar varias URLs de manera simultánea.
- **Proxies** (opcional): Se pueden especificar proxies para rotar las conexiones y evadir bloqueos.
- **Funciones de tamper** (opcional): Se pueden transformar las payloads para intentar evadir filtros o WAF (p. ej. `urlencode`, `uppercase`, etc.).
- **Salida en tiempo real** a un archivo de texto y/o **exportación JSON** con los resultados.

---

## Requisitos

1. **Python 3** (3.6 o superior recomendado).
2. Librerías incluidas en `requirements.txt` (principalmente `requests`, `colorama` y otras).

Para instalarlas:
```bash
pip install -r requirements.txt
```
> Si lo deseas, puedes usar entornos virtuales (por ejemplo con `venv`).

---

## Instalación y ejecución

1. **Clona o descarga** este repositorio en tu sistema:
   ```bash
   git clone https://github.com/tuusuario/tu-repo-sqli-scanner.git
   cd tu-repo-sqli-scanner
   ```
2. **Instala** las dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```
3. **Ejecuta** el script:
   ```bash
   python3 sql_scanner.py --file urls.txt
   ```
   Asegúrate de que `sql_scanner.py` (o el nombre que tenga tu archivo) sea el script principal.

---

## Uso y Parámetros

El script se controla a través de **argumentos**. Puedes ver la lista completa usando `-h` o `--help`:

```bash
python3 sql_scanner.py --help
```

A continuación, se describen todos los parámetros disponibles:

### `--file` (obligatorio)
- **Descripción**: Especifica la **ruta** del archivo que contiene las URLs a procesar, una por línea.
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt
  ```
  > Si no se proporciona, el script no sabrá qué URLs escanear.

### `--threads`
- **Descripción**: Indica el **número de hilos** (threads) que se usarán para procesar las URLs en paralelo.
- **Valor por defecto**: `5`.
- **Cuándo usarlo**: Si tienes muchas URLs y quieres acelerar el escaneo, puedes aumentar el número de hilos.  
  Si tu conexión o el servidor son frágiles, puedes reducirlo.
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --threads 10
  ```
  Con esto, usará 10 hilos en lugar de 5.

### `--min-delay` y `--max-delay`
- **Descripción**: Controlan un **retraso aleatorio** entre peticiones para evitar saturar el servidor o que un WAF detecte muchas solicitudes seguidas.
- **Valores por defecto**:
  - `--min-delay`: `0.05` (segundos)
  - `--max-delay`: `0.1` (segundos)
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --min-delay 0.1 --max-delay 0.5
  ```
  Se esperará entre 0.1 y 0.5 segundos tras cada request.

### `--output`
- **Descripción**: Archivo de **texto** donde se registran, **en tiempo real**, las vulnerabilidades detectadas.
- **Comportamiento**: 
  - Si no se especifica, la salida de hallazgos se mostrará solo en consola.
  - Si se especifica, cada vez que se detecte una posible vulnerabilidad se añadirá inmediatamente una línea al archivo.
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --output vulns.txt
  ```
  > Todos los hallazgos se irán agregando a `vulns.txt`.

### `--json-output`
- **Descripción**: Genera un reporte final en **formato JSON** con todos los hallazgos.
- **Cuándo usarlo**: Si quieres un **reporte estructurado** para procesarlo luego en otras herramientas.
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --json-output reporte.json
  ```
  Al final del escaneo, se creará (o sobrescribirá) el archivo `reporte.json` con la información de cada URL vulnerable.

### `--verbose`
- **Descripción**: Si se activa, **muestra información detallada** (códigos de estado, URL solicitada, errores ocurridos, etc.).
- **Uso**:
  ```bash
  python3 sql_scanner.py --file urls.txt --verbose
  ```
  Es útil para depurar o si quieres ver en vivo cómo avanza el escaneo.

### `--proxies`
- **Descripción**: Especifica un **archivo de texto** con una lista de proxies, **uno por línea**. El script seleccionará un proxy de manera aleatoria para cada petición.
- **Cuándo usarlo**: Si deseas:
  1. **Rotar IPs** y evitar bloqueos.
  2. No dejar un rastro claro de peticiones repetidas con la misma IP.
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --proxies proxies.txt
  ```

### `--tamper`
- **Descripción**: Permite **obfuscar** (tamper) los payloads antes de enviarlos, con el fin de evadir algunos filtros o WAF.
- **Uso**:
  - Se puede emplear **varias veces**. Por ejemplo, `--tamper urlencode --tamper space2comment`.
  - Cada valor corresponde a una **función de tamper** incluida en el script:
    - `uppercase`
    - `space2comment`
    - `escape_quotes`
    - `urlencode`
- **Ejemplo**:
  ```bash
  python3 sql_scanner.py --file urls.txt --tamper urlencode --tamper space2comment
  ```

---

## Ejemplos de ejecución

```bash
# Escaneo simple
python3 sql_scanner.py --file urls.txt

# Escaneo con salida JSON y retrasos definidos
python3 sql_scanner.py --file urls.txt --output vulns.txt --json-output salida.json --min-delay 0.1 --max-delay 0.5

# Escaneo con proxies y tamper
python3 sql_scanner.py --file urls.txt --proxies proxies.txt --tamper urlencode --tamper escape_quotes
```
=======
# SQLi 5c4nn3r

## Descripción
SQLi Scanner es una herramienta diseñada para probar inyecciones SQL en parámetros de URLs. Su propósito es identificar vulnerabilidades en aplicaciones web mediante una lista de payloads predefinidos.

---

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/c1ph3rbyt3/SQLiScanner.git
   cd SQLiScanner
   ```

2. **Instalar las dependencias necesarias:**
   Asegúrate de tener Python 3 instalado. Luego, instala las dependencias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

---

## Uso

El script se ejecuta desde la línea de comandos con diferentes parámetros opcionales para configurar su funcionamiento.

### Sintaxis básica
```bash
python SQLiScanner.py [opciones]
```

### Opciones disponibles

#### `-i` o `--input-file`
- **Descripción:** Especifica un archivo de texto que contiene una lista de URLs para probar.
- **Uso:**
  ```bash
  python SQLiScanner.py -i urls.txt
  ```

#### `-u` o `--url`
- **Descripción:** Especifica una única URL para probar.
- **Uso:**
  ```bash
  python SQLiScanner.py -u "http://example.com/page?id=1"
  ```

#### `-t` o `--threads`
- **Descripción:** Establece el número de hilos a utilizar para procesar múltiples URLs simultáneamente. El valor por defecto es 10.
- **Uso:**
  ```bash
  python SQLiScanner.py -i urls.txt -t 5
  ```

#### `-o` o `--output-file`
- **Descripción:** Especifica un archivo de salida donde se guardarán las URLs vulnerables encontradas.
- **Uso:**
  ```bash
  python SQLiScanner.py -i urls.txt -o resultados.json
  ```

### Ejemplo completo
```bash
python SQLiScanner -i urls.txt -t 8 -o vulnerables.json
```

Este comando:
1. Procesa las URLs listadas en el archivo `urls.txt`.
2. Utiliza 8 hilos para realizar las pruebas.
3. Guarda los resultados en el archivo `vulnerables.json`.

---

## Notas importantes
- Si no se especifica el parámetro `-o` o `--output-file`, los resultados solo se mostrarán en la consola y no se guardarán en un archivo.
- Asegúrate de contar con los permisos necesarios para realizar pruebas en las URLs proporcionadas.
>>>>>>> a86c5bb92802708b6faf0063ca5f48cd21d62a72

---

## Contacto

<<<<<<< HEAD
Desarrollado por: **C1ph3rByt3**  
Para contribuciones, sugerencias o errores, abre un *issue* en este repositorio o crea un *pull request*.
=======
Creado por: **C1ph3rByt3**
>>>>>>> a86c5bb92802708b6faf0063ca5f48cd21d62a72
