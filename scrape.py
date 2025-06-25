import os 
import re
import csv
import time 
import random 
import sqlite3
import funcionesAux as fc
from datetime import datetime
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.webdriver.common.by import By

def mercadona_csv(datos, nombre_archivo="output/dia.csv"):
    """
    Guarda los datos en un archivo CSV.

    Parámetros:
    datos -- Lista de diccionarios con los datos a guardar.
    nombre_archivo -- Nombre del archivo CSV a crear.
    """
    if not datos:
        print("No hay datos para guardar.")
        return
    
    columnas = datos[0].keys()
    existe_archivo = os.path.isfile(nombre_archivo)

    # Crear carpeta si no existe
    carpeta = os.path.dirname(nombre_archivo)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta)

    with open(nombre_archivo, 'a+' if existe_archivo else 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)

        if not existe_archivo:
            writer.writeheader()

        writer.writerows(datos)

def iniciar_driver():
    """Inicia el driver de Selenium con las configuraciones necesarias."""
    driver = Driver(
        browser="chrome",
        uc=True,
        headless=True,  # headless activo para entornos CI
        incognito=False,
        agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        do_not_track=True,
        undetectable=True
    )
    # driver.maximize_window()  # Comentado para evitar errores en headless
    return driver

def obtener_datos_productos(driver, categoria):
    """Obtiene los datos de los productos dentro de una categoría."""
    productos = []
    elemento_productos = fc.wait_for_elements(driver, By.CSS_SELECTOR, 'div.product-cell[data-testid="product-cell"]', multiple=True)
    print(f"Total productos encontrados: {len(elemento_productos)}")

    for anuncio in elemento_productos: 
        html_content = anuncio.get_attribute('innerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')

        img_element = soup.find('img')
        imagen = img_element['src'] if img_element else "Imagen no disponible"

        h4_element = soup.find('h4', class_="subhead1-r product-cell__description-name", attrs={"data-testid": "product-cell-name"})
        titulo = h4_element.text if h4_element else "Título no disponible"

        p_element = soup.find('p', class_="product-price__unit-price subhead1-b", attrs={"data-testid": "product-price"})
        if p_element is None:
            p_element = soup.find('p', class_="product-price__unit-price subhead1-b product-price__unit-price--discount", attrs={"data-testid": "product-price"})
        
        precio = p_element.text.replace(".", "").replace(",", ".").replace("€", "").strip() if p_element else "Precio no disponible"

        print(f"Producto: {titulo}\nImagen: {imagen}\nPrecio: {precio}")
        productos.append({
            'titulo': titulo,
            'imagen': imagen,
            'precio': precio,
            'categoria': categoria
        })
    return productos

def explorar_categorias(driver):
    """Explora las categorías en la página y extrae los datos de cada producto."""
    lista_productos = []
    
    categorias = fc.wait_for_elements(driver, By.CSS_SELECTOR, '.category-menu__header', multiple=True)
    
    for categoria in categorias: 
    try:
        nombre_categoria = categoria.text.replace(",", "")
        print(f"\nAnalizando categoría: {nombre_categoria}")
        time.sleep(random.uniform(0.5, 1))

        # Esperar a que desaparezca cualquier modal visible
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.modal, div[data-testid="modal"], div[data-testid="mask"]'))
            )
        except Exception as e:
            print(f"Modal aún visible. Intentando forzar su cierre. Error: {e}")
            try:
                boton_cerrar = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="close-modal"], .modal button.close')
                boton_cerrar.click()
                time.sleep(1)
            except:
                print("No se encontró botón de cierre. Ocultando modal con JavaScript.")
                driver.execute_script("""
                    document.querySelectorAll('div.modal, div[data-testid="modal"], div[data-testid="mask"]').forEach(el => el.remove());
                """)
                time.sleep(1)

        # Esperar a que la categoría esté clicable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[text()='{nombre_categoria}']"))
        )
        categoria.click()
        time.sleep(random.uniform(0.5, 1))

        # Continuar con subcategorías
        el_category = fc.wait_for_elements(driver, By.CSS_SELECTOR, 'li.category-menu__item.open', multiple=False)
        subcategorias = fc.wait_for_elements(el_category, By.CSS_SELECTOR, 'ul > li.category-item', multiple=True)

        for subcategoria in subcategorias:
            print(subcategoria.text)
            subcategoria.click()
            time.sleep(random.uniform(0.5, 1))
            productos = obtener_datos_productos(driver, nombre_categoria)
            lista_productos.extend(productos)

    except Exception as e:
        print(f"Error al analizar la categoría {nombre_categoria}: {e}")

    return lista_productos

if __name__ == "__main__":
    driver = iniciar_driver()
    try:
        fecha = datetime.now().date()
        print(f"Iniciando escaneo a fecha: {datetime.now()}")

        driver.get("https://tienda.mercadona.es/")
        # Aceptar cookies
        fc.click_element(driver, By.XPATH, "//button[normalize-space()='Aceptar']")
        time.sleep(2)
        
        # Navegar a la sección de categorías
        driver.get("https://tienda.mercadona.es/categories/112")
        
        # Extraer datos de las categorías y productos
        productos = explorar_categorias(driver)
        
        if productos:
            mercadona_csv(productos, f"output/mercadona_{fecha}.csv")
            print(f"Datos guardados en output/mercadona_{fecha}.csv")
        else:
            print("No se encontraron productos.")

    except Exception as e:
        print(f"Error durante el proceso de scraping: {e}")
    
    finally:
        driver.quit()
