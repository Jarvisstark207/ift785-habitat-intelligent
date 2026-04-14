"""
Tests unitaires — Configuration et fichiers d'infrastructure (Iteration 10)
"""

import os


class TestEnvExample:
    def test_env_example_exists(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".env.example")
        assert os.path.exists(path), ".env.example doit exister"

    def test_env_example_has_postgres_user(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".env.example")
        content = open(path).read()
        assert "POSTGRES_USER" in content

    def test_env_example_has_postgres_password(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".env.example")
        content = open(path).read()
        assert "POSTGRES_PASSWORD" in content

    def test_env_example_no_real_secrets(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".env.example")
        content = open(path).read()
        # Les valeurs exemples ne doivent pas contenir de vraies cles
        assert "sk-" not in content
        assert "eyJ" not in content  # JWT tokens

    def test_env_not_committed(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        gitignore_path = os.path.join(root, ".gitignore")
        if os.path.exists(gitignore_path):
            content = open(gitignore_path).read()
            assert ".env" in content, ".env doit etre dans .gitignore"


class TestDockerfileConfig:
    def test_dockerfile_exists(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "Dockerfile")
        assert os.path.exists(path), "Dockerfile doit exister"

    def test_dockerfile_uses_python_image(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "Dockerfile")
        content = open(path).read()
        assert "python:" in content.lower(), "Image Python officielle requise"

    def test_dockerignore_exists(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".dockerignore")
        assert os.path.exists(path), ".dockerignore doit exister"

    def test_dockerignore_excludes_venv(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".dockerignore")
        content = open(path).read()
        assert "venv" in content


class TestDockerComposeConfig:
    def test_compose_file_exists(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        assert os.path.exists(path), "docker-compose.yml doit exister"

    def test_compose_has_backend_service(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        assert "backend" in compose["services"]

    def test_compose_has_db_service(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        assert "db" in compose["services"]

    def test_compose_has_nginx_service(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        assert "nginx" in compose["services"]

    def test_compose_has_named_volumes(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        assert "volumes" in compose

    def test_compose_backend_depends_on_db(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        backend = compose["services"]["backend"]
        assert "depends_on" in backend

    def test_compose_db_has_healthcheck(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        db = compose["services"]["db"]
        assert "healthcheck" in db

    def test_compose_db_uses_postgres(self):
        import yaml
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        db = compose["services"]["db"]
        image = db.get("image", "")
        assert "postgres" in image
