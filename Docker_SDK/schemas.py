from pydantic import BaseModel
from typing import List, Optional


class MainContainerRequest(BaseModel):
    image: Optional[str] = None
    command: Optional[List[str]] = None
    name: str
    ports: Optional[dict] = None


class ContainerRequest(BaseModel):
    ContainerName: str


class RemoveContainerRequest(BaseModel):
    name: str
    force: Optional[bool] = False
    v: Optional[bool] = False


class BuildImage(BaseModel):
    tag: str


class PullImage(BaseModel):
    name: str


class CollectionName(BaseModel):
    CollectionName: str
