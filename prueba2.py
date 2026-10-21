import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def limpiar_nombre(texto):
    """Limpia caracteres inválidos para nombres de carpetas en Windows/Mac"""
    caracteres_invalidos = '<>:"/\\|?*'
    for char in caracteres_invalidos:
        texto = texto.replace(char, '')
    return texto.strip()

def esperar_descargas(directorio, timeout=60):
    tiempo_inicio = time.time()
    while True:
        if not os.path.exists(directorio): break
        if not any(archivo.endswith(".crdownload") for archivo in os.listdir(directorio)): break
        if time.time() - tiempo_inicio > timeout: break
        time.sleep(1)

DIRECTORIO_BASE = os.path.join(os.getcwd(), "Comites_Academicos_2026")
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
    # --- FASE 1: EXTRAER URLs Y CREAR CARPETAS PRINCIPALES ---
    driver.get("https://www.posgrado.unam.mx/comunidad-interna/comites-academicos-2026/")

    xpath_jornadas = "//h5/a[strong[contains(text(), 'Jornada')]]"
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, xpath_jornadas))
    )

    elementos_jornadas = driver.find_elements(By.XPATH, xpath_jornadas)
    datos_jornadas = []

    # Guardamos los datos en memoria antes de hacer cualquier clic o cambio de página
    for elemento in elementos_jornadas:
        nombre = elemento.text.strip()
        url = elemento.get_attribute("href")
        
        datos_jornadas.append({"nombre": nombre, "url": url})
        
        # Crear la carpeta principal de la jornada
        ruta_destino = os.path.join(DIRECTORIO_BASE, limpiar_nombre(nombre))
        os.makedirs(ruta_destino, exist_ok=True)
        print(f"Registrada: {nombre}")

    # --- FASE 2: NAVEGAR A CADA JORNADA Y DESCARGAR ARCHIVOS ---
    for jornada in datos_jornadas:
        print(f"\n--- Procesando {jornada['nombre']} ---")
        driver.get(jornada['url']) 
        
        ruta_jornada = os.path.join(DIRECTORIO_BASE, limpiar_nombre(jornada['nombre']))

        try:
            # Esperar a que carguen los contenedores de los programas (acordeones)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "gdlr-core-accordion-item-content-wrapper"))
            )
            
            # Obtener todos los programas de posgrado
            programas = driver.find_elements(By.CLASS_NAME, "gdlr-core-accordion-item-content-wrapper")

            for programa in programas:
                try:
                    # Extraer título del programa y limpiar el nombre para la carpeta
                    titulo_elemento = programa.find_element(By.XPATH, ".//h4")
                    nombre_programa = limpiar_nombre(titulo_elemento.text)
                    print(f"  -> Descargando: {nombre_programa}")

                    # 1. DESPLEGAR EL ACORDEÓN
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", titulo_elemento)
                    time.sleep(0.5)
                    titulo_elemento.click()
                    time.sleep(1) # Esperar animación

                    # 2. CREAR CARPETAS PARA ESTE PROGRAMA
                    ruta_alumnado = os.path.join(ruta_jornada, nombre_programa, "Alumnado")
                    ruta_tutores = os.path.join(ruta_jornada, nombre_programa, "Tutores")
                    os.makedirs(ruta_alumnado, exist_ok=True)
                    os.makedirs(ruta_tutores, exist_ok=True)

                    # 3. EXTRAER ENLACES DE 'ALUMNADO' (Columna 1)
                    driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ruta_alumnado})
                    enlaces_alumnado = programa.find_elements(By.XPATH, ".//table/tbody/tr[2]/td[1]//a")
                    
                    for enlace in enlaces_alumnado:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", enlace)
                        time.sleep(0.3)
                        enlace.click()
                    esperar_descargas(ruta_alumnado) 

                    # 4. EXTRAER ENLACES DE 'TUTORES' (Columna 2)
                    driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ruta_tutores})
                    enlaces_tutores = programa.find_elements(By.XPATH, ".//table/tbody/tr[2]/td[2]//a")
                    
                    for enlace in enlaces_tutores:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", enlace)
                        time.sleep(0.3)
                        enlace.click()
                    esperar_descargas(ruta_tutores)

                    # Cerrar el acordeón para mantener la página limpia (opcional)
                    titulo_elemento.click()
                    time.sleep(0.5)

                except Exception as e:
                    print(f"  [!] Error procesando el programa {nombre_programa if 'nombre_programa' in locals() else 'Desconocido'}: {e}")
                    continue 

        except Exception as e:
            print(f"No se encontraron programas o hubo un error en la jornada {jornada['nombre']}: {e}")

finally:
    print("\nProceso de extracción de PDFs finalizado con éxito.")
    time.sleep(3) 
    driver.quit()