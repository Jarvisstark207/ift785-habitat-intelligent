"""
Tests d'integration — Validation structure docker-compose.yml (Iteration 10)

Verifie que le compose file a la bonne structure sans lancer Docker.
"""

import os
import pytest
import yaml


ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
COMPOSE_PATH = os.path.join(ROOT, "docker-compose.yml")


@pytest.fixture
def compose():
    """Charge le docker-compose.yml."""
    with open(COMPOSE_PATH) as f:
        return yaml.safe_load(f)


class TestComposeStructure:
    def test_compose_file_parseable(self, compose):
        assert compose is not None

    def test_has_services_section(self, compose):
        assert "services" in compose

    def test_backend_service_exists(self, compose):
        assert "backend" in compose["services"]

    def test_db_service_exists(self, compose):
        assert "db" in compose["services"]

    def test_nginx_service_exists(self, compose):
        assert "nginx" in compose["services"]

    def test_backend_builds_from_dockerfile(self, compose):
        backend = compose["services"]["backend"]
        assert "build" in backend

    def test_db_uses_postgres_image(self, compose):
        db = compose["services"]["db"]
        image = db.get("image", "")
        assert "postgres" in image

    def test_nginx_uses_nginx_image(self, compose):
        nginx = compose["services"]["nginx"]
        image = nginx.get("image", "")
        assert "nginx" in image

    def test_named_volumes_declared(self, compose):
        assert "volumes" in compose
        volumes = compose["volumes"]
        assert len(volumes) >= 1

    def test_backend_depends_on_db(self, compose):
        backend = compose["services"]["backend"]
        depends = backend.get("depends_on", {})
        assert "db" in depends

    def test_db_has_healthcheck(self, compose):
        db = compose["services"]["db"]
        assert "healthcheck" in db

    def test_backend_has_healthcheck(self, compose):
        backend = compose["services"]["backend"]
        assert "healthcheck" in backend

    def test_backend_healthcheck_uses_health_endpoint(self, compose):
        backend = compose["services"]["backend"]
        hc_test = str(backend["healthcheck"].get("test", ""))
        assert "health" in hc_test

    def test_db_healthcheck_uses_pg_isready(self, compose):
        db = compose["services"]["db"]
        hc_test = str(db["healthcheck"].get("test", ""))
        assert "pg_isready" in hc_test

    def test_depends_on_has_condition(self, compose):
        backend = compose["services"]["backend"]
        depends = backend.get("depends_on", {})
        if isinstance(depends, dict) and "db" in depends:
            assert "condition" in depends["db"]


class TestDockerfileStructure:
    def test_dockerfile_exists(self):
        dockerfile_path = os.path.join(ROOT, "Dockerfile")
        assert os.path.exists(dockerfile_path)

    def test_dockerfile_exposes_port(self):
        dockerfile_path = os.path.join(ROOT, "Dockerfile")
        content = open(dockerfile_path).read()
        assert "EXPOSE" in content
        assert "8000" in content

    def test_dockerfile_has_cmd_or_entrypoint(self):
        dockerfile_path = os.path.join(ROOT, "Dockerfile")
        content = open(dockerfile_path).read()
        assert "CMD" in content or "ENTRYPOINT" in content

    def test_dockerfile_copies_requirements(self):
        dockerfile_path = os.path.join(ROOT, "Dockerfile")
        content = open(dockerfile_path).read()
        assert "requirements.txt" in content
