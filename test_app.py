import importlib
import os
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(scope="module")
def service():
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "AUTH_SERVICE_URL": "http://auth.test",
        },
    ), patch("psycopg2.pool.SimpleConnectionPool"):
        return importlib.import_module("app")


def test_health_returns_ok(service):
    response = service.app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_rule_requires_authorization(service):
    response = service.app.test_client().post(
        "/rules",
        json={"flag_name": "new-ui", "rules": {"type": "PERCENTAGE", "value": 50}},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Authorization header obrigatório"}


def test_create_rule_rejects_missing_fields(service, monkeypatch):
    monkeypatch.setattr(
        service.requests,
        "get",
        lambda *args, **kwargs: Mock(status_code=200),
    )

    response = service.app.test_client().post(
        "/rules",
        headers={"Authorization": "Bearer test-key"},
        json={"flag_name": "new-ui"},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "'flag_name' e 'rules' (JSON) são obrigatórios"
    }
