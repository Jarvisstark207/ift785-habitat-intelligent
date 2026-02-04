# app/__init__.py
"""
Pont de compatibilité.

Dans ce projet, il y a :
- un package `app/`
- un module `app.py`

Quand un test fait `from app import app`, Python importe par défaut le package `app/`
et NON le fichier `app.py`. Donc sans ce pont, `app` n'existe pas et les tests échouent.

Ce fichier charge dynamiquement `app.py` et expose l'objet FastAPI `app`.
"""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_APP_PY_PATH = Path(__file__).resolve().parent.parent / "app.py"

spec = spec_from_file_location("app_py_module", _APP_PY_PATH)
_module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(_module)

# Exposer l'instance FastAPI attendue par les tests : `from app import app`
app = _module.app
