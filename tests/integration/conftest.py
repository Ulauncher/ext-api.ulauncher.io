# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

import json
import os
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import boto3
import jwt
import pytest
import urllib3
from botocore.config import Config
from botocore.exceptions import ClientError
from pymongo import MongoClient
from urllib3.filepost import encode_multipart_formdata

PRIVATE_KEY_PATH = Path(__file__).parent / "fixtures" / "auth" / "private_key.pem"
USER_ID = "github|integration-user"


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = urllib3.PoolManager()

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        multipart_fields: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> urllib3.response.BaseHTTPResponse:
        request_headers = dict(headers or {})
        body: bytes | None = None

        if json_body is not None:
            request_headers["Content-Type"] = "application/json"
            body = json.dumps(json_body).encode("utf-8")
        elif multipart_fields is not None:
            body, content_type = encode_multipart_formdata(multipart_fields)
            request_headers["Content-Type"] = content_type

        return self.http.request(
            method,
            f"{self.base_url}{path}",
            body=body,
            headers=request_headers,
            retries=False,
        )

    @staticmethod
    def parse_json(response: urllib3.response.BaseHTTPResponse) -> dict[str, Any]:
        payload = response.data.decode("utf-8")
        return cast("dict[str, Any]", json.loads(payload) if payload else {})


def _wait_until(check: Callable[[], bool], timeout: float = 60.0, interval: float = 1.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            if check():
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(interval)

    raise RuntimeError(f"Timed out while waiting for integration dependency: {last_error}")


@pytest.fixture(scope="session")
def api_client() -> ApiClient:
    return ApiClient(os.environ["API_BASE_URL"])


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient[dict[str, Any]]:
    return MongoClient(os.environ["MONGODB_CONNECTION"])


@pytest.fixture(scope="session")
def mongo_db(mongo_client: MongoClient[dict[str, Any]]) -> Any:
    return mongo_client[os.environ["DB_NAME"]]


@pytest.fixture(scope="session")
def s3_client() -> Any:
    boto3_client: Any = boto3.client
    return boto3_client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ["AWS_DEFAULT_REGION"],
        config=Config(s3={"addressing_style": os.environ.get("S3_ADDRESSING_STYLE", "path")}),  # type: ignore[arg-type]
    )


@pytest.fixture(scope="session", autouse=True)
def integration_environment(api_client: ApiClient, s3_client: Any) -> None:
    bucket_name = os.environ["EXT_IMAGES_BUCKET_NAME"]

    def s3_ready() -> bool:
        s3_client.list_buckets()
        return True

    def api_ready() -> bool:
        response = api_client.request("GET", "/extensions")
        return response.status == 200

    _wait_until(s3_ready)
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3_client.create_bucket(Bucket=bucket_name)

    _wait_until(api_ready)


@pytest.fixture(autouse=True)
def reset_test_state(mongo_db: Any, s3_client: Any) -> Iterator[None]:
    bucket_name = os.environ["EXT_IMAGES_BUCKET_NAME"]

    mongo_db.Extensions.delete_many({})
    objects = s3_client.list_objects_v2(Bucket=bucket_name).get("Contents", [])
    if objects:
        s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]})

    yield

    mongo_db.Extensions.delete_many({})
    objects = s3_client.list_objects_v2(Bucket=bucket_name).get("Contents", [])
    if objects:
        s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]})


@pytest.fixture(scope="session")
def auth_header() -> dict[str, str]:
    token = jwt.encode(
        {"sub": USER_ID, "aud": os.environ["AUTH0_CLIENT_ID"]},
        PRIVATE_KEY_PATH.read_text(encoding="utf-8"),
        algorithm="RS256",
    )
    return {"Authorization": f"Bearer {token}"}
