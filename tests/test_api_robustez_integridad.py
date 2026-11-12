"""
Pruebas de integridad de datos y robustez de la API.
Aqui miro los casos raros: correos con mayusculas y espacios, campos que faltan,
tipos de dato equivocados y cuerpos que no son un objeto JSON.

Los dos casos marcados con xfail son hallazgos reales: la API acepta un semestre
decimal o booleano cuando deberia rechazarlo. Quedan documentados y, cuando se
corrija el defecto, el xfail se quita y la prueba debe pasar.

Para correr solo estas:  python -m pytest -m robustez -v
"""
import uuid

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.robustez]
TIMEOUT = 10
PROGRAMA = "Ingenieria de Sistemas"
MSG_SEMESTRE = "El semestre debe ser un numero entre 1 y 10"


def correo_unico():
    return f"rob_{uuid.uuid4().hex[:8]}@ceto.edu.co"


@pytest.fixture
def estudiante_valido():
    return {"nombre": "Ana Ruiz", "correo": correo_unico(), "programa": PROGRAMA, "semestre": 4}


# ---------------------------- Integridad de datos ----------------------------
def test_rob01_correo_se_normaliza_a_minusculas_y_sin_espacios(api_url, estudiante_valido):
    base = estudiante_valido["correo"]
    estudiante_valido["correo"] = f"  {base.upper()}  "
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 201
    assert r.json()["correo"] == base  # se guardo limpio y en minusculas
    requests.delete(f"{api_url}/{r.json()['id']}", timeout=TIMEOUT)


def test_rob02_correo_duplicado_ignora_mayusculas(api_url, estudiante_valido):
    creado = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT).json()
    repetido = dict(estudiante_valido, correo=estudiante_valido["correo"].upper())
    r = requests.post(api_url, json=repetido, timeout=TIMEOUT)
    assert r.status_code == 409
    requests.delete(f"{api_url}/{creado['id']}", timeout=TIMEOUT)


def test_rob03_nombre_solo_con_espacios_se_rechaza(api_url, estudiante_valido):
    estudiante_valido["nombre"] = "      "
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 422
    assert "nombre" in r.json()["errores"]


def test_rob04_nombre_se_guarda_sin_espacios_sobrantes(api_url, estudiante_valido):
    estudiante_valido["nombre"] = "   Luis Pinto   "
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 201
    assert r.json()["nombre"] == "Luis Pinto"
    requests.delete(f"{api_url}/{r.json()['id']}", timeout=TIMEOUT)


# ---------------------------- Robustez ante datos raros ----------------------------
def test_rob05_campos_faltantes_reportan_todos_los_errores(api_url):
    r = requests.post(api_url, json={}, timeout=TIMEOUT)
    assert r.status_code == 422
    assert set(r.json()["errores"]) == {"nombre", "correo", "programa", "semestre"}


@pytest.mark.parametrize("campo", ["nombre", "correo", "programa", "semestre"])
def test_rob06_un_campo_nulo_devuelve_422(api_url, estudiante_valido, campo):
    estudiante_valido[campo] = None
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 422
    assert campo in r.json()["errores"]


@pytest.mark.parametrize("cuerpo", ['[1, 2, 3]', '"texto"', '42'], ids=["lista", "texto", "numero"])
def test_rob07_json_que_no_es_objeto_devuelve_400(api_url, cuerpo):
    r = requests.post(api_url, data=cuerpo, headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
    assert r.status_code == 400


def test_rob08_json_mal_formado_devuelve_400(api_url):
    r = requests.post(api_url, data="{esto no cierra", headers={"Content-Type": "application/json"},
                      timeout=TIMEOUT)
    assert r.status_code == 400


@pytest.mark.parametrize("id_raro", ["abc", "0", "-5"], ids=["texto", "cero", "negativo"])
def test_rob09_ids_raros_devuelven_404(api_url, id_raro):
    assert requests.get(f"{api_url}/{id_raro}", timeout=TIMEOUT).status_code == 404


# ---------------------------- Hallazgos (defectos reales) ----------------------------
@pytest.mark.xfail(reason="HALLAZGO H1: la API acepta semestre decimal (4.5) y lo trunca a 4", strict=True)
def test_rob10_semestre_decimal_deberia_rechazarse(api_url, estudiante_valido):
    estudiante_valido["semestre"] = 4.5
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 422
    assert r.json()["errores"]["semestre"] == MSG_SEMESTRE


@pytest.mark.xfail(reason="HALLAZGO H2: la API acepta semestre booleano (true) y lo guarda como 1", strict=True)
def test_rob11_semestre_booleano_deberia_rechazarse(api_url, estudiante_valido):
    estudiante_valido["semestre"] = True
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 422
