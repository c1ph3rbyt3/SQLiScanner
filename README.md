# SQLi Scanner

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

---

## Contacto

Creado por: **C1ph3rByt3**
