import os

os.environ["NEXUS_DATABASE_URL"] = "sqlite:////private/tmp/nexus-api-test.db"
os.environ["NEXUS_SECRET_KEY"] = "test-secret-key-with-more-than-thirty-two-characters"
os.environ["NEXUS_SEED_DEMO"] = "true"
os.environ["NEXUS_CORS_ORIGINS"] = "http://localhost:3000"

from fastapi.testclient import TestClient

from nexus_api.main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/v1/auth/login",
        json={"email": "founder@nexus.local", "password": "NexusPass123!"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_seeded_user_can_access_workforce() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get("/v1/organizations", headers=headers)
        assert response.status_code == 200, response.text
        organizations = response.json()
        assert organizations
        detail = organizations[0]
        assert detail["organization"]["name"] == "Nexus Manufacturing"
        root_agents = detail["hierarchy"]
        assert root_agents[0]["agent"]["role_key"] == "ceo_agent"


def test_agent_run_creates_trace_and_analytics() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        organizations = client.get("/v1/organizations", headers=headers).json()
        organization_id = organizations[0]["organization"]["id"]
        agents = client.get(f"/v1/organizations/{organization_id}/agents", headers=headers).json()
        ceo = next(agent for agent in agents if agent["role_key"] == "ceo_agent")
        run_response = client.post(
            f"/v1/organizations/{organization_id}/agents/{ceo['id']}/runs",
            headers=headers,
            json={"objective": "Assess supplier risk and prepare an approved mitigation plan."},
        )
        assert run_response.status_code == 200, run_response.text
        run = run_response.json()
        assert run["trace_id"]
        assert run["confidence"] > 0
        analytics = client.get(f"/v1/organizations/{organization_id}/analytics", headers=headers)
        assert analytics.status_code == 200, analytics.text
        assert analytics.json()["active_agents"] >= 20

