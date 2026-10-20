import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def esperar_descargas(directorio, timeout=60):
    """Espera a que no haya archivos .crdownload en el directorio."""
    tiempo_inicio = time.time()
    while True:
        if not os.path.exists(directorio):
            break
        archivos = os.listdir(directorio)
        if not any(archivo.endswith(".crdownload") for archivo in archivos):
            break
        if time.time() - tiempo_inicio > timeout:
            print(f"Timeout en directorio: {directorio}")
            break
        time.sleep(1)

DIRECTORIO_BASE = os.path.join(os.getcwd(), "Formatos_Posgrado")
os.makedirs(DIRECTORIO_BASE, exist_ok=True)

# Configuración de Chrome para forzar descargas
opciones = webdriver.ChromeOptions()
preferencias = {
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
}
opciones.add_experimental_option("prefs", preferencias)
driver = webdriver.Chrome(options=opciones)

try:
    driver.get("https://www.posgrado.unam.mx/comunidad-interna/servicios-administrativos/formatos-de-procesos/")
    
    # Buscar los <li> que contienen la clase 'gdlr-core-with-hover'
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//li[contains(@class, 'gdlr-core-with-hover')]"))
    )

    # Obtener todos los contenedores de los formatos
    elementos = driver.find_elements(By.XPATH, "//li[contains(@class, 'gdlr-core-with-hover')]")

    for elemento in elementos:
        try:
            # Extraer el nombre de la carpeta
            span_texto = elemento.find_element(By.XPATH, ".//span[contains(@class, 'gdlr-core-icon-list-content')]")
            nombre_carpeta = span_texto.text.strip()
            
            if not nombre_carpeta:
                continue

            # Limpiar caracteres inválidos para carpetas
            for char in '<>:"/\\|?*':
                nombre_carpeta = nombre_carpeta.replace(char, '')

            ruta_destino = os.path.join(DIRECTORIO_BASE, nombre_carpeta)
            os.makedirs(ruta_destino, exist_ok=True)

            # Cambiar ruta de descarga mediante CDP
            driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': ruta_destino
            })

            enlace = elemento.find_element(By.XPATH, ".//a")
            
            # Asegurar que el elemento esté en pantalla antes de hacer clic
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", enlace)
            time.sleep(0.5) 
            
            enlace.click()
            time.sleep(1) 

            # Esperar descarga completa
            esperar_descargas(ruta_destino)
            print(f"Descargado: {nombre_carpeta}")

        except Exception as e:
            print(f"Error procesando un elemento: {e}")
            continue

finally:
    driver.quit()
    print("Proceso finalizado.")