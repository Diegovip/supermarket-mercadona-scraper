import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_elements(driver, by, value, multiple=False, timeout=15):
    """
    Espera hasta que uno o varios elementos estén presentes en el DOM.
    
    Parámetros:
    - driver: instancia del navegador.
    - by: selector de tipo By (por ejemplo, By.CSS_SELECTOR).
    - value: string del selector.
    - multiple: True si se esperan varios elementos, False para uno solo.
    - timeout: tiempo máximo de espera (por defecto 15 segundos).
    
    Retorna:
    - Elemento o lista de elementos.
    """
    if multiple:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )
    else:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

def click_element(driver, by, value, timeout=15):
    """
    Espera a que el elemento esté visible y haga clic sobre él.
    
    Parámetros:
    - driver: instancia del navegador.
    - by: tipo de selector.
    - value: string del selector.
    - timeout: segundos de espera antes de lanzar excepción.
    """
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()
