from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
import docker
import os
import time
import requests
from pydantic import BaseModel
import logging
from typing import List, Optional
from utils.s3 import S3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
s3utils = S3(os.environ["access_key"], os.environ["secret_key"])

while True:
    try:
        client = docker.from_env(timeout=5)
        if client:
            break 
    except (docker.errors.DockerException, requests.exceptions.RequestException) as e:
        logging.info("Trying to connect the docker server")
        time.sleep(10)

app = FastAPI()

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


def get_container(container_name: str):
    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error accessing container: {str(e)}")


def upload_to_s3(fileobj: UploadFile):
    try:
        path = s3utils.upload_file(fileobj, fileobj.filename)
        logging.info(f"Upload complete. Path: {path}")
        return {"path_to_object": path}
    except Exception as e:
        logging.exception("Error occurred during S3 upload")
        raise HTTPException(status_code=500, detail="Error uploading file to S3")


def create_docker_container(request: MainContainerRequest, volumes: Optional[dict] = None):
    container_params = {
        "image": request.image,
        "name": request.name,
        "ports": request.ports,
        "detach": True,
        "volumes": volumes,  # Added volumes for mapping
    }
    if request.command:
        container_params["command"] = request.command
    try:
        container = client.containers.create(**container_params)
        logging.info(f"Container {request.name} created successfully")
        return container
    except Exception as e:
        logging.exception(f"Error creating the container {request.name}")
        raise HTTPException(status_code=500, detail=f"Error creating container: {str(e)}")


def determine_image(file_extension: str) -> str:
    if file_extension == ".py":
        return "python:3.9-slim"
    elif file_extension == ".java":
        return "openjdk:11"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")


@app.post("/upload_s3_execute")
async def upload_s3_execute(fileobj: UploadFile = File(...)):
    try:
        file_extension = os.path.splitext(fileobj.filename)[-1].lower()
        container_name = f"container_1"
        local_path = f"/tmp/{fileobj.filename}"

        # Save file locally
        with open(local_path, "wb") as f:
            f.write(await fileobj.read())

        # Determine image and set container params
        image = determine_image(file_extension)
        client.images.pull(image)
        volumes = {"/tmp/": {"bind": "/tmp/", "mode": "rw"}}
        command = ["/bin/sh", "-c", f"python /tmp/{os.path.basename(local_path)}"]
        ports = {"8080/tcp": 8080}

        container_request = MainContainerRequest(
            image=image,
            command=command,
            name=container_name,
            ports=ports,
        )

        # Create and run container
        container = create_docker_container(container_request, volumes=volumes)
        container.start()
        container.wait()
        logs = container.logs().decode("utf-8")

        # Clean up container and upload to S3
        container.remove(force=True)
        file_object = upload_to_s3(fileobj)

        return {"logs": logs, "file_path": file_object}
    except Exception as e:
        logging.exception("Error in upload_s3_execute function")
        raise HTTPException(status_code=500, detail=f"Error in upload_s3_execute: {str(e)}")

@app.post("/create_container")
def create_container(request: MainContainerRequest):
    return create_docker_container(request)
@app.post("/pull_image")
def pull_image(request: PullImage):
    try:
        name = client.images.pull(request.name)
        return {f"Image Pulled {name}"}
    except Exception as e:
        logging.error("Error pulling the Image: {e}")

@app.get("/containers")
def list_containers():
    containers = client.containers.list(all=True)
    return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]

@app.get("/list_images")
def get_images_list():
    try:
        images = client.images.list()
        return [{"id": img.id, "tags": img.tags} for img in images]
    except docker.errors.APIError as e:
        logging.error(f"Error while getting the list {e}")
        raise HTTPException(status_code=500, detail=f"Error listing images: {str(e)}")

@app.get("/stopped_containers")
def list_stopped_containers():
    containers = client.containers.list(filters={"status":"exited"})
    return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]

@app.post("/stop_container", response_model=dict)
def stop_container(request: ContainerRequest):
    containerObj = get_container(request.ContainerName)
    try:
        containerObj.stop()
        return {"message": f"Container {request.ContainerName} stopped successfully"}
    except Exception as e:
        logging.error(f" error Stoping the container {request.ContainerName}: {e}")

@app.post("/get_logs/")        
def get_logs_container(request: ContainerRequest):
    containerObj = get_container(request.ContainerName)
    try:
        return {"container_name": request.ContainerName, "logs": containerObj.logs()}
    except Exception as e:
        logging.error(f"Error getting the logs of the container {request.ContainerName}: {e}")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@app.post("/start_container") 
def start_container(request: ContainerRequest):
    containerObj = get_container(request.ContainerName)
    try:
        containerObj.start()
        return {f"contianer {request.ContainerName} started"}
    except Exception as e:
        logging.error(f"Error when starting the container {request.ContainerName}: {e}")

@app.post("/container_details", response_model=dict)
def get_container_details(request: ContainerRequest):
    try:
        containerObj = get_container(request.ContainerName)
        return containerObj.attrs
    except Exception as e:
        logging.error("Error when getting the details of the container {name}: {e}")

@app.post("/remove_container", response_model=dict)
def remove_container(request: RemoveContainerRequest):
    container = get_container(request.name)
    try:
        container.remove(force=request.force, v=request.v)
        logging.info(f"Container {request.name} removed successfully")
        return {"message": f"Container {request.name} removed successfully"}
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error removing container: {str(e)}")

@app.post("/build_image")
async def build_image(fileobj: UploadFile = File(...), obj: BuildImage = Depends()):
    try:
        buildimage, logs = client.images.build(fileobj=fileobj.file, tag=obj.tag)
        logging.info("Image built successfully")
        return {"message": "Image built successfully", "image_id": buildimage.id}
    except docker.errors.APIError as e:
        logging.exception("Error building image")
        raise HTTPException(status_code=500, detail=f"Error building image: {str(e)}")
