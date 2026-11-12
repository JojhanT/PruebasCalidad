"""
Pruebas del formulario de inscripcion con Selenium y Page Object.
Los casos de error salen de data/casos_formulario.csv, asi que para agregar uno
solo hay que sumar una fila y no tocar el codigo.

Para correr solo estas:  python -m pytest -m ui -v
"""
import csv
import uuid
from pathlib import Path

import pytest

from pages.inscripcion_page import InscripcionPage, ListadoPage

pytestmark = pytest.mark.ui
DATOS = Path(__file__).resolve().parent.parent / "data" / "casos_formulario.csv"


def cargar_casos_invalidos():
    # utf-8 para que las tildes no se dañen en Windows
    with open(DATOS, encoding="utf-8", newline="") as f:
        return [pytest.param(fila, id=fila["caso"]) for fila in csv.DictReader(f)]


def test_web01_inscripcion_exitosa_aparece_en_listado(driver, base_url, evidencia):
    correo = f"carlos_{uuid.uuid4().hex[:6]}@ceto.edu.co"
    pagina = InscripcionPage(driver, base_url).abrir()
    evidencia("01_formulario_vacio")

    pagina.inscribir("Carlos Gomez", correo, "Ingenieria de Sistemas", 5)
    evidencia("02_resultado")

    assert pagina.mensaje_exito().startswith("Inscripcion exitosa. Codigo: EST-")

    # ahora miro que de verdad quedo en el listado
    listado = ListadoPage(driver, base_url).abrir()
    evidencia("03_listado")
    assert correo in listado.correos()


@pytest.mark.parametrize("caso", cargar_casos_invalidos())
def test_web02_a_05_formulario_muestra_error_por_campo(driver, base_url, caso):
    pagina = InscripcionPage(driver, base_url).abrir()
    pagina.inscribir(caso["nombre"], caso["correo"], caso["programa"], caso["semestre"])

    assert pagina.error_de(caso["campo_error"]) == caso["mensaje_esperado"]
    # solo debe fallar el campo que esperamos, ninguno mas
    assert len(pagina.errores()) == 1


def test_web06_conserva_datos_tras_un_error(driver, base_url, evidencia):
    pagina = InscripcionPage(driver, base_url).abrir()
    pagina.inscribir("Maria Lopez", "correo-malo", "Ingenieria Industrial", 6)

    assert pagina.error_de("correo") == "Correo invalido"
    evidencia("error_conserva_datos")
    # lo que escribio el usuario no se debe perder
    assert pagina.valor_de("nombre") == "Maria Lopez"
    assert pagina.valor_de("semestre") == "6"
