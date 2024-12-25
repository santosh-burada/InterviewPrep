import docker.errors
from schemas import MainContainerRequest
import docker
import requests

import time, os
from typing import Optional
from utils.s3 import S3
from utils.logger_config import setup_logging


s3utils = S3(os.environ["access_key"], os.environ["secret_key"])

logging = setup_logging()


def client():
    while True:
        try:
            client = docker.from_env(timeout=5)
            if client:
                break
        except (
            docker.errors.DockerException,
            requests.exceptions.RequestException,
        ) as e:
            logging.info("Trying to connect the docker server")
            time.sleep(10)
    return client


client = client()


def get_container(container_name: str):
    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound as e:
        logging.exception(f"error getting the container: {e}")


def upload_to_s3(fileobj):
    try:
        path = s3utils.upload_file(fileobj, fileobj.filename)
        logging.info(f"Upload complete. Path: {path}")
        return {"path_to_object": path}
    except Exception as e:
        logging.exception("Error occurred during S3 upload")


def create_docker_container(
    request: MainContainerRequest, volumes: Optional[dict] = None
):
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


def determine_image(file_extension: str) -> str:
    if file_extension == ".py":
        return "python:3.9-slim"
    elif file_extension == ".java":
        return "openjdk:11"
    else:
        logging.exception("Unsupported file type")


def file_upload_execute(file_extension, local_path):

    # Determine image and set container params
    image = determine_image(file_extension)
    client.images.pull(image)
    container_name = "container_1"
    volumes = {"/tmp/": {"bind": "/tmp/", "mode": "rw"}}
    command = ["/bin/sh", "-c", f"python /tmp/{os.path.basename(local_path)}"]
    # ports = {"8080/tcp": 8080}

    container_request = MainContainerRequest(
        image=image,
        command=command,
        name=container_name,
        # ports=ports,
    )

    # Create and run container
    container = create_docker_container(container_request, volumes=volumes)
    container.start()
    container.wait()
    logs = container.logs().decode("utf-8")
    # send the logs to mongoDb

    # Clean up container and upload to S3
    container.remove(force=True)
    # use background task to do this.

    return logs


def pull_image(name):
    try:
        name = client.images.pull(name)
        return {f"Image Pulled {name}"}
    except:
        logging.exception("Error in upload_s3_execute function")


def list_containers():
    containers = client.containers.list(all=True)
    return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]


def list_images():
    try:
        images = client.images.list()
        return [{"id": img.id, "tags": img.tags} for img in images]
    except docker.errors.APIError as e:
        logging.error(f"Error while getting the list {e}")


def stopped_containers():
    try:
        containers = client.containers.list(filters={"status": "exited"})
        return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]
    except Exception as e:
        logging.error(f"Error while getting the list {e}")


def stop_container(name):
    containerObj = get_container(name)
    try:
        containerObj.stop()
        return {"message": f"Container {name} stopped successfully"}
    except (Exception, docker.errors.NotFound, docker.errors.APIError) as e:
        logging.error(f" error Stoping the container {name}: {e}")


def get_logs(name):
    try:
        containerObj = get_container(name)
        return {"container_name": name, "logs": containerObj.logs()}
    except (Exception, docker.errors.NotFound, docker.errors.APIError) as e:
        logging.error(f"Error getting the logs of the container {name}: {e}")


def start_container(name):
    containerObj = get_container(name)
    try:
        containerObj.start()
        return {f"contianer {name} started"}
    except (Exception, docker.errors.NotFound, docker.errors.APIError) as e:
        logging.error(f"Error when starting the container {name}: {e}")


def container_details(name):
    try:
        containerObj = get_container(name)
        return containerObj.attrs
    except (Exception, docker.errors.NotFound, docker.errors.APIError) as e:
        logging.error(f"Error when getting the details of the container {name}: {e}")


def container_remove(name, force, v):
    container = get_container(name)
    try:
        container.remove(force=force, v=v)
        logging.info(f"Container {name} removed successfully")
        return {"message": f"Container {name} removed successfully"}
    except (Exception, docker.errors.NotFound, docker.errors.APIError) as e:
        logging.info(f"Container {name} removed unsuccessfully. Error: {e}")


def container_run(container_params):
    try:
        existing_container = get_container(container_params["name"])
        existing_container.start()
        return {"message": f"Container {container_params['name']} started successfully"}
    except docker.errors.NotFound:

        container = client.containers.run(**container_params)
        return {
            "message": f"Container {container_params['name']} is running",
            "id": container.id,
        }


def image_build(file, tag):
    try:
        buildimage, logs = client.images.build(fileobj=file, tag=tag)
        logging.info("Image built successfully")
        return {"message": "Image built successfully", "image_id": buildimage.id}
    except docker.errors.APIError as e:
        logging.exception("Error building image")
