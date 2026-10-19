import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def esperar_descargas(directorio, timeout=60):
    """
    Espera a que terminen las descargas en un directorio.
    Chrome usa la extensión .crdownload mientras el archivo se está bajando.
    """
    tiempo_inicio = time.time()
    while True:
        # Busca si hay algún archivo temporal de descarga en proceso
        archivos = os.listdir(directorio)
        si_descargando = any(archivo.endswith(".crdownload") for archivo in archivos)
        
        if not si_descargando:
            break # Todas las descargas han terminado
            
        if time.time() - tiempo_inicio > timeout:
            print(f"Tiempo de espera agotado para las descargas en {directorio}")
            break
            
        time.sleep(1) # Esperar un segundo antes de volver a comprobar

# 1. Directorio base donde se crearán todas las carpetas
DIRECTORIO_BASE = os.path.join(os.getcwd(), "Descargas_PDFs")
os.makedirs(DIRECTORIO_BASE, exist_ok=True)

# 2. Configurar Chrome para que descargue PDFs en vez de abrirlos
opciones = webdriver.ChromeOptions()
preferencias = {
    "download.prompt_for_download": False, # No preguntar dónde guardar
    "plugins.always_open_pdf_externally": True # ¡VITAL! Fuerza la descarga del PDF
}
opciones.add_experimental_option("prefs", preferencias)

# Inicializar el navegador
driver = webdriver.Chrome(options=opciones)

try:
    # 3. Navegar a la página (Sustituye por tu URL real)
    driver.get("file:///C:/Users/SerSocial-2503226-US/Documents/AutomatizaciónSelenium/pagina_tabla.html")
    
    # OPCIONAL: Si hay login, debes programar los pasos aquí antes de seguir.

    # 4. Esperar a que la tabla esté visible
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//table"))
    )

    # 5. Obtener todas las filas de la tabla (ajusta el XPath a tu HTML real)
    # Ejemplo asume una tabla estándar con <tbody> y filas <tr>
    filas = driver.find_elements(By.XPATH, "//table/tbody/tr")

    for fila in filas:
        # Obtener las celdas (columnas) de esa fila específica
        columnas = fila.find_elements(By.TAG_NAME, "td")
        
        if not columnas:
            continue # Saltar si es una fila vacía o de encabezado

        # 6. Extraer el nombre para la carpeta (asumiendo que es la 1ra columna)
        # Reemplazamos caracteres que no son válidos para nombres de carpetas en Windows/Mac
        nombre_carpeta = columnas[0].text.strip()
        caracteres_invalidos = '<>:"/\\|?*'
        for char in caracteres_invalidos:
            nombre_carpeta = nombre_carpeta.replace(char, '')

        ruta_destino = os.path.join(DIRECTORIO_BASE, nombre_carpeta)
        os.makedirs(ruta_destino, exist_ok=True)

        # 7. Magia de CDP: Cambiar la carpeta de descarga sobre la marcha para esta iteración
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': ruta_destino
        })

        # 8. Buscar los botones/enlaces de PDF en esta fila
        # Aquí debes inspeccionar tu página. Por ejemplo, buscar etiquetas <a> o botones
        enlaces_pdf = fila.find_elements(By.XPATH, ".//a") # Ajustar selector

        for enlace in enlaces_pdf:
            # Filtrar si es necesario (ej: if "pdf" in enlace.get_attribute("href"))
            driver.execute_script("arguments[0].scrollIntoView();", enlace) # Asegurar que sea visible
            time.sleep(0.5) # Pequeña pausa de estabilización
            enlace.click()
            time.sleep(1) # Dar tiempo a que el navegador registre el inicio de descarga

        # 9. Esperar a que terminen de bajar los PDFs antes de pasar a la siguiente fila
        esperar_descargas(ruta_destino)
        print(f"Descargados archivos para el registro: {nombre_carpeta}")

finally:
    driver.quit()
    print("Proceso finalizado.")