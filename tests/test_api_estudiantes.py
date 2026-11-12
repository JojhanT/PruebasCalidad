"""
Pruebas de la API REST de estudiantes.

Como las armé:
  - cada prueba crea sus propios datos con un correo distinto, asi ninguna depende de otra
  - las fixtures preparan y limpian, como el BeforeEach y AfterEach de JUnit

"""
import uuid

import pytest
import requests

pytestmark = pytest.mark.api
TIMEOUT = 10  # toda peticion lleva limite de tiempo, si no se puede quedar colgada
PROGRAMA = "Ingenieria de Sistemas"
MSG_SEMESTRE = "El semestre debe ser un numero entre 1 y 10"


def correo_unico():
    """Correo nuevo en cada llamada, para que no choquen entre pruebas."""
    return f"est_{uuid.uuid4().hex[:8]}@ceto.edu.co"


@pytest.fixture
def estudiante_valido():
    return {"nombre": "Ana Ruiz", "correo": correo_unico(), "programa": PROGRAMA, "semestre": 4}


@pytest.fixture
def estudiante_creado(api_url, estudiante_valido):
    """Crea un estudiante antes de la prueba y lo borra cuando termina."""
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 201, "Fallo la preparacion, no se pudo crear el estudiante"
    creado = r.json()
    yield creado
    requests.delete(f"{api_url}/{creado['id']}", timeout=TIMEOUT)


# ---------------------------- Casos que deben salir bien ----------------------------
def test_api01_crear_estudiante_devuelve_201_y_el_recurso(api_url, estudiante_valido):
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 201
    assert r.headers["Content-Type"].startswith("application/json")
    cuerpo = r.json()
    assert isinstance(cuerpo["id"], int)
    assert cuerpo["correo"] == estudiante_valido["correo"]
    assert cuerpo["nombre"] == "Ana Ruiz"
    requests.delete(f"{api_url}/{cuerpo['id']}", timeout=TIMEOUT)  # dejo todo limpio


def test_api02_consultar_estudiante_por_id(api_url, estudiante_creado):
    r = requests.get(f"{api_url}/{estudiante_creado['id']}", timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.json() == estudiante_creado


def test_api03_listar_contiene_al_estudiante_creado(api_url, estudiante_creado):
    r = requests.get(api_url, timeout=TIMEOUT)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert estudiante_creado in r.json()


def test_api04_filtrar_por_programa(api_url, estudiante_creado):
    r = requests.get(api_url, params={"programa": PROGRAMA}, timeout=TIMEOUT)
    assert r.status_code == 200
    lista = r.json()
    assert estudiante_creado in lista
    assert all(e["programa"] == PROGRAMA for e in lista)


def test_api04b_filtro_con_programa_sin_registros_devuelve_lista_vacia(api_url, estudiante_creado):
    r = requests.get(api_url, params={"programa": "Programa Inexistente"}, timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.json() == []


def test_api05_eliminar_devuelve_204_y_luego_404(api_url, estudiante_valido):
    creado = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT).json()
    url = f"{api_url}/{creado['id']}"

    r = requests.delete(url, timeout=TIMEOUT)
    assert r.status_code == 204
    assert r.text == ""
    # confirmo que de verdad se borro
    assert requests.get(url, timeout=TIMEOUT).status_code == 404


# ---------------------------- Casos de error ----------------------------
@pytest.mark.parametrize("campo, valor, mensaje", [
    ("nombre", "", "El nombre es obligatorio (minimo 3 caracteres)"),
    ("nombre", "Al", "El nombre es obligatorio (minimo 3 caracteres)"),
    ("correo", "correo-sin-arroba", "Correo invalido"),
    ("programa", "Medicina", "Programa no valido"),
    ("semestre", 0, MSG_SEMESTRE),
    ("semestre", 11, MSG_SEMESTRE),
    ("semestre", "cuatro", MSG_SEMESTRE),
], ids=["nombre_vacio", "nombre_2_caracteres", "correo_invalido", "programa_inexistente",
        "semestre_0", "semestre_11", "semestre_texto"])
def test_api06_a_10_datos_invalidos_devuelven_422(api_url, estudiante_valido, campo, valor, mensaje):
    estudiante_valido[campo] = valor  # dañamos un solo campo y el resto queda bien
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 422
    assert r.json()["errores"][campo] == mensaje


@pytest.mark.parametrize("semestre", [1, 10], ids=["limite_inferior_1", "limite_superior_10"])
def test_api_valores_limite_validos_se_aceptan(api_url, estudiante_valido, semestre):
    estudiante_valido["semestre"] = semestre
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)
    assert r.status_code == 201
    assert r.json()["semestre"] == semestre
    requests.delete(f"{api_url}/{r.json()['id']}", timeout=TIMEOUT)


def test_api11_correo_duplicado_devuelve_409(api_url, estudiante_creado, estudiante_valido):
    r = requests.post(api_url, json=estudiante_valido, timeout=TIMEOUT)  # mismo correo de nuevo
    assert r.status_code == 409
    assert r.json()["errores"]["correo"] == "El correo ya esta registrado"


def test_api12_cuerpo_no_json_devuelve_400(api_url):
    r = requests.post(api_url, data="esto no es json", headers={"Content-Type": "text/plain"},
                      timeout=TIMEOUT)
    assert r.status_code == 400
    assert "error" in r.json()


def test_api13_id_inexistente_devuelve_404(api_url):
    r = requests.get(f"{api_url}/999999", timeout=TIMEOUT)
    assert r.status_code == 404
    assert r.json()["error"] == "Estudiante no encontrado"


def test_api13b_eliminar_id_inexistente_devuelve_404(api_url):
    assert requests.delete(f"{api_url}/999999", timeout=TIMEOUT).status_code == 404
