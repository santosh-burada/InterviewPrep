from fastapi import FastAPI
import docker
from pydantic import BaseModel
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
client = docker.from_env()
# print(client)
app = FastAPI()

class CreateContainerRequest(BaseModel):
    image: str
    command: list = None
    name: str
class RunContainerRequest(BaseModel):
    image: str
    command: list= None
    name: str
    ports: dict = None
@app.get("/containers")
def list_containers():
    return client.containers.list()

@app.get("/stopped_containers")
def list_stopped_containers():
    print(client.containers.list(filters={"status":"exited"}))
@app.get("/container_details/{container_name}")
def get_container_details(container_name: str):
    try:
        containerObj = client.containers.get(container_name)
        for key, value in containerObj.attrs.items():
            print(f"{key}: {value}")
    except Exception as e:
        logging.error("Error when getting the details of the container {name}: {e}")
# 2 api
@app.post("/create_container")
def create_container(request: CreateContainerRequest):
    try:
        client.containers.create(image=request.image, command=request.command, name=request.name, detach=True)
        logging.info(f"Container {request.name} is Created")
        return {f"contianer Created"}
    except Exception as e:
        logging.error(f"error creating the container {request.name}: {e}")

@app.get("/stop_container")
def stop_container(container_name: str):
    try:
        containerObj = client.containers.get(container_name)
        containerObj.stop()
    except Exception as e:
        logging.error(f" error Stoping the container {container_name}: {e}")

@app.post("/run_container")
def run_container(request: RunContainerRequest):
    try:
        client.containers.run(image=request.image,command=request.command, name = request.name, ports = request.ports)
    except Exception as e:
        logging.error(f"Error ocuured during the container {request.name} run: {e}")

@app.get("/get_logs/{container_name}")        
def get_logs_container(container_name: str):
    try:
        containerObj = client.containers.get(container_name)
        logging.info(f"logs of container {container_name}:{containerObj.logs()}")
    except Exception as e:
        logging.error(f"Error getting the logs of the container {container_name}: {e}")
@app.get("/start_container/{container_name}") 
def start_container(container_name: str):
    try:
        containerObj = client.containers.get(container_name)
        containerObj.start()
    except Exception as e:
        logging.error(f"Error when starting the container {container_name}: {e}")
@app.get("/stop_container/{container_name}") 
def stop_container(container_name: str):
    try:
        containerObj = client.containers.get(container_name)
        containerObj.stop()
    except Exception as e:
        logging.error(f"Error when starting the container {container_name}: {e}")
# 3 api
@app.get("/list_images")
def get_images_list():
    try:
        images = client.images.list()
        return [{"id": img.id, "tags": img.tags} for img in images]
    except docker.errors.APIError as e:
        logging.error(f"Error while getting the list {e}")
