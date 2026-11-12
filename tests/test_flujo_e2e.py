"""
Flujos completos que mezclan la web y la API.
La idea es comprobar que lo que se hace por un lado se ve por el otro.

Para correr solo estos:  python -m pytest -m e2e -v
"""
import uuid

import pytest
import requests

from pages.inscripcion_page import InscripcionPage, ListadoPage

pytestmark = [pytest.mark.ui, pytest.mark.e2e]
TIMEOUT = 10


def correo(prefijo):
    return f"{prefijo}_{uuid.uuid4().hex[:6]}@ceto.edu.co"


def test_e2e01_inscripcion_web_queda_registrada_en_api(driver, base_url, api_url, evidencia):
    mail = correo("web")
    InscripcionPage(driver, base_url).abrir().inscribir("Sofia Mejia", mail, "Ingenieria Industrial", 7)
    evidencia("inscripcion_web")

    # inscribo por la pantalla y reviso por la API
    estudiantes = requests.get(api_url, timeout=TIMEOUT).json()
    registro = next((e for e in estudiantes if e["correo"] == mail), None)
    assert registro is not None, "La inscripcion web no aparece en la API"
    assert registro["semestre"] == 7


def test_e2e02_registro_creado_por_api_aparece_en_listado_web(driver, base_url, api_url, evidencia):
    mail = correo("api")
    r = requests.post(api_url, json={"nombre": "Pedro Diaz", "correo": mail,
                                     "programa": "Ingenieria de Sistemas", "semestre": 2}, timeout=TIMEOUT)
    assert r.status_code == 201
    # creo por la API y reviso en la pantalla
    listado = ListadoPage(driver, base_url).abrir()
    evidencia("listado_con_registro_api")
    assert mail in listado.correos()


def test_e2e03_correo_duplicado_en_web_muestra_error(driver, base_url, evidencia):
    mail = correo("dup")
    pagina = InscripcionPage(driver, base_url).abrir()
    pagina.inscribir("Laura Rios", mail, "Ingenieria de Sistemas", 3)
    assert pagina.mensaje_exito().startswith("Inscripcion exitosa")

    # el segundo intento con el mismo correo debe rebotar
    pagina = InscripcionPage(driver, base_url).abrir()
    pagina.inscribir("Laura Rios", mail, "Ingenieria de Sistemas", 3)
    evidencia("duplicado")
    assert pagina.error_de("correo") == "El correo ya esta registrado"


def test_e2e04_eliminar_por_api_quita_el_registro_del_listado_web(driver, base_url, api_url):
    mail = correo("del")
    creado = requests.post(api_url, json={"nombre": "Nora Paz", "correo": mail,
                                          "programa": "Ingenieria Industrial", "semestre": 9},
                           timeout=TIMEOUT).json()
    assert mail in ListadoPage(driver, base_url).abrir().correos()
    assert requests.delete(f"{api_url}/{creado['id']}", timeout=TIMEOUT).status_code == 204
    assert mail not in ListadoPage(driver, base_url).abrir().correos()
