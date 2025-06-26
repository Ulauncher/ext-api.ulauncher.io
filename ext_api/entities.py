import datetime
from typing import NotRequired, TypedDict


class Extension(TypedDict):
    ID: str
    User: str
    GithubUrl: str
    ProjectPath: str
    Name: str
    Description: str
    DeveloperName: str
    Images: list[str]
    SupportedVersions: list[str]
    GithubStars: int
    Published: bool
    CreatedAt: NotRequired[datetime.datetime]
    UpdatedAt: NotRequired[datetime.datetime]


class Migration(TypedDict):
    Version: int
    CreatedAt: datetime.datetime


class RepoInfo(TypedDict):
    stargazers_count: int
    default_branch: str


class Manifest(TypedDict):
    api_version: str
    name: str
    description: str
    authors: str
