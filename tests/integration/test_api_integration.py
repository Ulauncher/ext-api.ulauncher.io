import os
from typing import Any, cast

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="integration tests require Podman Compose")
USER_ID = "github|integration-user"


def _create_extension(api_client: Any, auth_header: dict[str, str], github_url: str, name: str) -> None:
    upload_response = api_client.request(
        "POST",
        "/upload-images",
        headers=auth_header,
        multipart_fields={"file": ("shot.png", b"fake-image-bytes", "image/png")},
    )
    assert upload_response.status == 200

    create_response = api_client.request(
        "POST",
        "/extensions",
        headers=auth_header,
        json_body={
            "GithubUrl": github_url,
            "Name": name,
            "Description": f"{name} description",
            "DeveloperName": "Integration Suite",
            "Images": cast("list[str]", api_client.parse_json(upload_response)["data"]),
        },
    )
    assert create_response.status == 200


def test_extension_happy_path(api_client: Any, auth_header: dict[str, str], mongo_db: Any, s3_client: Any) -> None:
    list_response = api_client.request("GET", "/extensions")
    assert list_response.status == 200
    assert api_client.parse_json(list_response)["data"] == []

    upload_response = api_client.request(
        "POST",
        "/upload-images",
        headers=auth_header,
        multipart_fields={"file": ("shot.png", b"fake-image-bytes", "image/png")},
    )
    assert upload_response.status == 200
    upload_payload = api_client.parse_json(upload_response)
    uploaded_urls = cast("list[str]", upload_payload["data"])
    assert isinstance(uploaded_urls, list)
    assert len(uploaded_urls) == 1

    image_url = uploaded_urls[0]
    assert image_url.startswith(os.environ["S3_PUBLIC_BASE_URL"])
    bucket_contents = cast(
        "list[dict[str, str]]",
        s3_client.list_objects_v2(Bucket=os.environ["EXT_IMAGES_BUCKET_NAME"]).get("Contents", []),
    )
    assert len(bucket_contents) == 1
    assert bucket_contents[0]["Key"].startswith(f"{USER_ID}/")

    create_response = api_client.request(
        "POST",
        "/extensions",
        headers=auth_header,
        json_body={
            "GithubUrl": "https://github.com/stub-owner/stub-repo",
            "Name": "Stub Extension",
            "Description": "Initial description",
            "DeveloperName": "Integration Suite",
            "Images": uploaded_urls,
        },
    )
    assert create_response.status == 200
    created_payload = cast("dict[str, Any]", api_client.parse_json(create_response)["data"])
    assert created_payload["ID"] == "github-stub-owner-stub-repo"
    assert created_payload["SupportedVersions"] == ["5", "4"]
    assert mongo_db.Extensions.count_documents({}) == 1

    filtered_response = api_client.request("GET", "/extensions?versions=5")
    assert filtered_response.status == 200
    filtered_payload = api_client.parse_json(filtered_response)
    assert len(cast("list[Any]", filtered_payload["data"])) == 1

    my_extensions_response = api_client.request("GET", "/my/extensions", headers=auth_header)
    assert my_extensions_response.status == 200
    assert len(cast("list[Any]", api_client.parse_json(my_extensions_response)["data"])) == 1

    update_response = api_client.request(
        "PATCH",
        "/extensions/github-stub-owner-stub-repo",
        headers=auth_header,
        json_body={
            "Name": "Stub Extension Updated",
            "Description": "Updated description",
            "DeveloperName": "Integration Suite",
            "Images": uploaded_urls,
        },
    )
    assert update_response.status == 200
    updated_payload = cast("dict[str, Any]", api_client.parse_json(update_response)["data"])
    assert updated_payload["Name"] == "Stub Extension Updated"

    stored_extension = cast(
        "dict[str, Any] | None", mongo_db.Extensions.find_one({"ID": "github-stub-owner-stub-repo"})
    )
    assert stored_extension is not None
    assert stored_extension["Name"] == "Stub Extension Updated"
    assert stored_extension["User"] == USER_ID

    delete_response = api_client.request("DELETE", "/extensions/github-stub-owner-stub-repo", headers=auth_header)
    assert delete_response.status == 204
    assert mongo_db.Extensions.count_documents({}) == 0

    missing_response = api_client.request("GET", "/extensions/github-stub-owner-stub-repo")
    assert missing_response.status == 404

    bucket_contents = cast(
        "list[dict[str, str]]",
        s3_client.list_objects_v2(Bucket=os.environ["EXT_IMAGES_BUCKET_NAME"]).get("Contents", []),
    )
    assert bucket_contents == []


def test_extensions_can_be_filtered_by_api_version(api_client: Any, auth_header: dict[str, str]) -> None:
    _create_extension(api_client, auth_header, "https://github.com/stub-owner/stub-repo", "Stub Extension")
    _create_extension(api_client, auth_header, "https://github.com/stub-owner/legacy-repo", "Legacy Extension")

    response = api_client.request("GET", "/extensions?versions=3")
    assert response.status == 200

    payload = api_client.parse_json(response)
    data = cast("list[dict[str, Any]]", payload["data"])
    assert len(data) == 1
    assert data[0]["ID"] == "github-stub-owner-legacy-repo"
    assert data[0]["SupportedVersions"] == ["3"]


def test_extensions_can_be_searched_by_project_path_and_description(
    api_client: Any, auth_header: dict[str, str]
) -> None:
    _create_extension(api_client, auth_header, "https://github.com/stub-owner/stub-repo", "Stub Extension")
    _create_extension(api_client, auth_header, "https://github.com/stub-owner/legacy-repo", "Legacy Extension")

    description_response = api_client.request("GET", "/extensions?q=legacy")
    assert description_response.status == 200
    description_payload = api_client.parse_json(description_response)
    description_data = cast("list[dict[str, Any]]", description_payload["data"])
    assert len(description_data) == 1
    assert description_data[0]["ID"] == "github-stub-owner-legacy-repo"

    project_path_response = api_client.request("GET", '/extensions?q="stub-owner/stub-repo"')
    assert project_path_response.status == 200
    project_path_payload = api_client.parse_json(project_path_response)
    project_path_data = cast("list[dict[str, Any]]", project_path_payload["data"])
    assert len(project_path_data) == 1
    assert project_path_data[0]["ID"] == "github-stub-owner-stub-repo"
