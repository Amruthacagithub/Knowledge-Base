def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "components" in data


def test_version_endpoint(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "knowledge-base"
    assert "version" in data
    assert "commit_sha" in data
    assert "environment" in data


def test_k8s_liveness_probe(client):
    r = client.get("/api/health/live")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_k8s_startup_probe(client):
    r = client.get("/api/health/startup")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "started"


def test_k8s_readiness_probe(client):
    r = client.get("/api/health/ready")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert "components" in data


def test_prometheus_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "knowledge_base_http_requests_total" in r.text or "Prometheus client" in r.text

