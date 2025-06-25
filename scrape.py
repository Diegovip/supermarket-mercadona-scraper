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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def mercadona_csv(datos, nombre_archivo="output/dia.csv"):
    if not datos:
        print("No hay datos para guardar.")
        return
    
    columnas = datos[0].keys()
    existe_archivo = os.path.isfile(nombre_archivo)

    carpeta = os.path.dirname(nombre_archivo)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta)

    with open(nombre_archivo, 'a+' if existe_archivo else 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        if not existe_archivo:
            writer.writeheader()
        writer.writerows(datos)

def iniciar_driver():
    driver = Driver(
        browser="chrome",
        uc=True,
        headless=True,
        incognito=False,
        agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        do_not_track=True,
        undetectable=True
    )
    return driver

def obtener_datos_productos(driver, categoria):
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
    lista_productos = []
    categorias = fc.wait_for_elements(driver, By.CSS_SELECTOR, '.category-menu__header', multiple=True)

    for categoria in categorias:
        try:
            nombre_categoria = categoria.text.replace(",", "")
            print(f"\nAnalizando categoría: {nombre_categoria}")
            time.sleep(random.uniform(0.3, 0.6))

            # Esperar o eliminar modales que bloquean la vista
            try:
                WebDriverWait(driver, 4).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.modal, div[data-testid="modal"], div[data-testid="mask"]'))
                )
            except:
                print("Modal sigue visible, ejecutando JavaScript para eliminarlo.")
                driver.execute_script("""
                    document.querySelectorAll('div.modal, div[data-testid="modal"], div[data-testid="mask"]').forEach(el => el.remove());
                """)
                time.sleep(1)

            # Scroll al elemento y esperar a que sea clicable
            driver.execute_script("arguments[0].scrollIntoView(true);", categoria)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{nombre_categoria}']")))

            # Segundo intento de limpieza antes del clic (por si reaparece)
            driver.execute_script("""
                document.querySelectorAll('div.modal, div[data-testid="modal"], div[data-testid="mask"]').forEach(el => el.remove());
            """)
            time.sleep(0.5)

            categoria.click()
            print(f"✓ Clic realizado en categoría: {nombre_categoria}")
            time.sleep(random.uniform(0.5, 1))

            el_category = fc.wait_for_elements(driver, By.CSS_SELECTOR, 'li.category-menu__item.open', multiple=False)
            subcategorias = fc.wait_for_elements(el_category, By.CSS_SELECTOR, 'ul > li.category-item', multiple=True)

            for subcategoria in subcategorias:
                print(f" > Subcategoría: {subcategoria.text}")
                subcategoria.click()
                time.sleep(random.uniform(0.5, 1))
                productos = obtener_datos_productos(driver, nombre_categoria)
                lista_productos.extend(productos)

        except Exception as e:
            print(f"⚠️ Error al analizar la categoría {nombre_categoria}: {e}")
            driver.save_screenshot(f"errors/error_{nombre_categoria}.png")

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

        productos = explorar_categorias(driver)

        if productos:
            mercadona_csv(productos, f"output/mercadona_{fecha}.csv")
            print(f"Datos guardados en output/mercadona_{fecha}.csv")
        else:
            print("No se encontraron productos.")

    except Exception as e:
        print(f"❌ Error durante el proceso de scraping: {e}")
    finally:
        driver.quit()
