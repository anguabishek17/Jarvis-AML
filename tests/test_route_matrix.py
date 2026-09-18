from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_route_matrix_endpoints():
    with open("jarvis_custom_test.csv", "r", encoding="utf-8") as f:
        csv_text = f.read()

    # 1. Validation GET and POST (with and without trailing slash)
    res_get = client.get("/api/investigate/validate")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "READY"

    res_get_slash = client.get("/api/investigate/validate/")
    assert res_get_slash.status_code == 200

    res_post = client.post("/api/investigate/validate", json={"csv_text": csv_text})
    assert res_post.status_code == 200
    report = res_post.json()
    assert report["total_rows"] == 15
    assert report["valid_rows"] == 15
    assert report["invalid_rows"] == 0
    assert report["is_acceptable_for_analysis"] is True

    res_post_slash = client.post("/api/investigate/validate/", json={"csv_text": csv_text})
    assert res_post_slash.status_code == 200

    # 2. Custom Pipeline GET and POST (with and without trailing slash)
    res_custom_get = client.get("/api/investigate/custom")
    assert res_custom_get.status_code == 200

    res_custom_post = client.post("/api/investigate/custom", json={"csv_text": csv_text, "dataset_name": "Test Run"})
    assert res_custom_post.status_code == 200
    case_data = res_custom_post.json()
    assert "CUSTOM-" in case_data["case_id"]
    assert len(case_data["graph"]["nodes"]) == 14
    assert len(case_data["graph"]["edges"]) == 15
