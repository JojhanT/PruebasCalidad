"""
Page Objects del modulo de inscripciones.
Aqui queda el como se maneja cada pagina, o sea los localizadores y las acciones.
Las pruebas solo dicen que se debe verificar, por eso aqui no hay asserts.
"""
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class InscripcionPage:
    NOMBRE = (By.ID, "nombre")
    CORREO = (By.ID, "correo")
    PROGRAMA = (By.ID, "programa")
    SEMESTRE = (By.ID, "semestre")
    BOTON = (By.ID, "btn-inscribir")
    EXITO = (By.ID, "mensaje-exito")
    ERRORES = (By.CSS_SELECTOR, ".error")

    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.url = f"{base_url}/inscripcion"
        self.wait = WebDriverWait(driver, timeout)

    def abrir(self):
        self.driver.get(self.url)
        self.wait.until(EC.visibility_of_element_located(self.NOMBRE))
        return self

    def _escribir(self, localizador, valor):
        campo = self.driver.find_element(*localizador)
        campo.clear()
        campo.send_keys(str(valor))

    def inscribir(self, nombre, correo, programa, semestre):
        self._escribir(self.NOMBRE, nombre)
        self._escribir(self.CORREO, correo)
        if programa:  # es una lista desplegable, por eso va con Select y no con send_keys
            Select(self.driver.find_element(*self.PROGRAMA)).select_by_visible_text(programa)
        self._escribir(self.SEMESTRE, semestre)
        boton = self.driver.find_element(*self.BOTON)
        boton.click()
        # Espero a que la pagina se recargue, o sea a que el boton viejo desaparezca.
        # En plena recarga Chrome a veces suelta un error pasajero, lo ignoro y reintento.
        WebDriverWait(self.driver, 10, ignored_exceptions=(WebDriverException,)).until(
            EC.staleness_of(boton)
        )

    def valor_de(self, campo):
        """Lo que tiene escrito un campo ahora mismo, sirve para ver si se conserva tras un error."""
        return self.wait.until(EC.visibility_of_element_located((By.ID, campo))).get_attribute("value")

    def mensaje_exito(self):
        return self.wait.until(EC.visibility_of_element_located(self.EXITO)).text

    def errores(self):
        return [e.text for e in self.driver.find_elements(*self.ERRORES)]

    def error_de(self, campo):
        return self.wait.until(EC.visibility_of_element_located((By.ID, f"error-{campo}"))).text


class ListadoPage:
    FILAS = (By.CSS_SELECTOR, "#tabla-estudiantes tbody tr.fila-estudiante")
    TOTAL = (By.ID, "total")

    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.url = f"{base_url}/estudiantes"
        self.wait = WebDriverWait(driver, timeout)

    def abrir(self):
        self.driver.get(self.url)
        self.wait.until(EC.visibility_of_element_located(self.TOTAL))
        return self

    def _columna(self, indice):
        filas = self.driver.find_elements(*self.FILAS)
        return [f.find_elements(By.TAG_NAME, "td")[indice].text for f in filas]

    def codigos(self):
        return self._columna(0)

    def correos(self):
        """Los correos, que van en la tercera columna."""
        return self._columna(2)

    def total(self):
        return int(self.driver.find_element(*self.TOTAL).text.split(":")[1])
