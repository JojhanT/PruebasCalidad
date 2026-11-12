"""
Flujos de punta a punta de integridad de datos y consistencia entre capas.
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


def test_e2e05_correo_en_mayusculas_se_guarda_en_minusculas(driver, base_url, api_url, evidencia):
    mail = correo("mayus")
    InscripcionPage(driver, base_url).abrir().inscribir("Rosa Vega", mail.upper(), "Ingenieria Industrial", 4)
    evidencia("correo_en_mayusculas")
    guardado = [e["correo"] for e in requests.get(api_url, timeout=TIMEOUT).json()]
    assert mail in guardado  # la API lo guardo en minusculas


def test_e2e06_duplicado_creado_por_api_se_rechaza_en_web(driver, base_url, api_url, evidencia):
    mail = correo("dupapi")
    r = requests.post(api_url, json={"nombre": "Hugo Cano", "correo": mail,
                                     "programa": "Ingenieria de Sistemas", "semestre": 5}, timeout=TIMEOUT)
    assert r.status_code == 201
    pagina = InscripcionPage(driver, base_url).abrir()
    pagina.inscribir("Hugo Cano", mail, "Ingenieria de Sistemas", 5)
    evidencia("duplicado_creado_por_api")
    assert pagina.error_de("correo") == "El correo ya esta registrado"


def test_e2e07_total_del_listado_web_coincide_con_la_api(driver, base_url, api_url):
    mail = correo("total")
    requests.post(api_url, json={"nombre": "Eva Mora", "correo": mail,
                                 "programa": "Ingenieria Industrial", "semestre": 3}, timeout=TIMEOUT)
    total_api = len(requests.get(api_url, timeout=TIMEOUT).json())
    assert ListadoPage(driver, base_url).abrir().total() == total_api
