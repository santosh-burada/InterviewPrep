from fastapi import FastAPI, HTTPException
import docker
from pydantic import BaseModel
import logging
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
client = docker.from_env()
# print(client)
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
    fileobj: str
    tag: str
def get_container(container_name: str):
    """Retrieve a container object by name or raise an exception."""
    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error accessing container: {str(e)}")

@app.get("/containers")
def list_containers():
    containers= client.containers.list(all=True)
    
    return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]

@app.get("/stopped_containers")
def list_stopped_containers():
    print(client.containers.list(filters={"status":"exited"}))

@app.post("/container_details", response_model=dict)
def get_container_details(request: ContainerRequest):
    try:
        containerObj = get_container(request.ContainerName)
        return containerObj.attrs
    except Exception as e:
        logging.error("Error when getting the details of the container {name}: {e}")

@app.post("/create_container")
def create_container(request: MainContainerRequest):
    try:
        container_params = {
            "image": request.image,
            "name": request.name,
            "ports": request.ports,
            "detach": True
        }
        if request.command:  
            container_params["command"] = request.command
        client.containers.create(**container_params)
        logging.info(f"Container {request.name} is Created")
        return {f"contianer Created"}
    except Exception as e:
        logging.error(f"error creating the container {request.name}: {e}")

@app.post("/stop_container", response_model=dict)
def stop_container(request: ContainerRequest):
    containerObj = get_container(request.ContainerName)
    try:
        containerObj.stop()
        return {"message": f"Container {request.ContainerName} stopped successfully"}
    except Exception as e:
        logging.error(f" error Stoping the container {request.ContainerName}: {e}")

@app.post("/run_container")
def run_container(request: MainContainerRequest):
    try:
        container_params = {
            "image": request.image,
            "name": request.name,
            "ports": request.ports,
            "detach": True
        }
        if request.command:  # Add command only if explicitly provided
            container_params["command"] = request.command
        try:
            existing_container = get_container(request.name)
            existing_container.start()
            return {"message": f"Container {request.name} started successfully"}
            # logging.info(f"Container {request.name} already exists. ports ar {existing_container.attrs}.")  
            # if request.ports:
            #     logging.info(f"Container {request.name} already exists. Removing it.")
            #     existing_container.stop()
            #     existing_container.remove()
            # else:
            #     logging.info(f"Container {request.name} already exists. Removing it.")
            #     existing_container.start()
            #     return {"message": f"Container {request.name} started successfully"}
        except HTTPException as e:
            if e.status_code != 404:
                raise

        container = client.containers.run(**container_params)
        return {"message": f"Container {request.name} is running", "id": container.id}
    except Exception as e:
        logging.error(f"Error ocuured during the container {request.name} run: {e}")

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

@app.post("/remove_container", response_model=dict)
def remove_container(request: RemoveContainerRequest):
    """Remove a container."""
    container = get_container(request.name)
    try:
        container.remove(force=request.force, v=request.v)
        logging.info(f"Container {request.name} removed successfully")
        return {"message": f"Container {request.name} removed successfully"}
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error removing container: {str(e)}")

@app.get("/list_images")
def get_images_list():
    try:
        images = client.images.list()
        return [{"id": img.id, "tags": img.tags} for img in images]
    except docker.errors.APIError as e:
        logging.error(f"Error while getting the list {e}")
        raise HTTPException(status_code=500, detail=f"Error listing images: {str(e)}")
    
#### Images ####

@app.get("/build_image")
def build_image(request: BuildImage):
    try:
        buildimage = client.images.build(**request)
        logging.info("Image built successfully")
        return {"message": "Image built successfully", "image_id": buildimage.id}
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error building image: {str(e)}")
    
