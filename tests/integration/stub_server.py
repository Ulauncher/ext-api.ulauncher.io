# pyright: reportUnknownVariableType=false

import json
import os
from pathlib import Path
from typing import Any

from bottle import Bottle, HTTPResponse, response, run

FIXTURES_DIR = Path(__file__).parent / "fixtures"
AUTH_DIR = FIXTURES_DIR / "auth"
GITHUB_DIR = FIXTURES_DIR / "github"

app = Bottle()


def _json_fixture(name: str) -> str:
    return (GITHUB_DIR / name).read_text(encoding="utf-8")


@app.get("/pem")  # type: ignore[misc]
def pem() -> HTTPResponse:
    return HTTPResponse(
        body=(AUTH_DIR / "certificate.pem").read_text(encoding="utf-8"),
        headers={"Content-Type": "application/x-pem-file"},
    )


@app.get("/repos/<owner>/<repo>")  # type: ignore[misc]
def repo(owner: str, repo: str) -> str:
    if (owner, repo) not in {("stub-owner", "stub-repo"), ("stub-owner", "legacy-repo")}:
        response.status = 404
        return json.dumps({"message": "Not Found"})
    return _json_fixture(f"{repo}-repo.json")


@app.get("/raw/<owner>/<repo>/<commit>/<filename>")  # type: ignore[misc]
def raw(owner: str, repo: str, commit: str, filename: str) -> str:
    if (
        (owner, repo) == ("stub-owner", "stub-repo")
        and commit == "main"
        and filename in {"manifest.json", "versions.json"}
    ):
        return _json_fixture(f"stub-{filename}")

    if (owner, repo) == ("stub-owner", "legacy-repo") and commit == "main" and filename == "manifest.json":
        return _json_fixture("legacy-manifest.json")

    if (owner, repo) == ("stub-owner", "legacy-repo") and commit == "main" and filename == "versions.json":
        return _json_fixture("legacy-versions.json")

    response.status = 404
    return json.dumps({"message": "Not Found"})


if __name__ == "__main__":
    bottle_run: Any = run
    bottle_run(app=app, host=os.getenv("STUB_HOST", "0.0.0.0"), port=int(os.getenv("STUB_PORT", "18080")))
