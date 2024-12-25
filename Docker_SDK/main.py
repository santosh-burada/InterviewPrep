from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
import os
from utils.s3 import S3
from schemas import *
from handlers import *
from db import MongoDB

app = FastAPI()
mongo = MongoDB(db_name="docker_sdk")
collection_name = mongo.create_collection("test_collection")


@app.post("/upload_s3_execute")
async def upload_s3_execute(background_tasks: BackgroundTasks, fileobj: UploadFile = File(...)):

    try:
        file_extension = os.path.splitext(fileobj.filename)[-1].lower()
        local_path = f"/tmp/{fileobj.filename}"

        # Save file locally
        with open(local_path, "wb") as f:
            f.write(await fileobj.read())

        logs = file_upload_execute(file_extension, local_path)
        file_object = upload_to_s3(fileobj)  # use background task to do this.
        inserted_id = mongo.insert({"logs": logs}, "test_collection")
        return {"logs": logs, "path_to_file": file_object, "inserted_id": inserted_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in upload_s3_execute: {str(e)}"
        )


@app.post("/run_container")
def run_container(request: MainContainerRequest):
    try:
        container_params = {
            "image": request.image,
            "name": request.name,
            "ports": request.ports,
            "detach": True,
        }
        if request.command:  # Add command only if explicitly provided
            container_params["command"] = request.command
        return container_run(container_params)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ocuured during the container {request.name} run: {e}",
        )


@app.post("/create_container")
def create_container(request: MainContainerRequest):
    try:
        return create_docker_container(request)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in upload_s3_execute: {str(e)}"
        )


@app.post("/pull_image")
def image_pull(request: PullImage):
    try:
        return pull_image(request.name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in upload_s3_execute: {str(e)}"
        )


@app.get("/containers")
def containers_list():
    return list_containers()


@app.get("/list_images")
def get_images_list():
    try:
        return list_images()
    except:
        raise HTTPException(status_code=500, detail=f"Error listing images")


@app.get("/stopped_containers")
def list_stopped_containers():
    try:
        return stopped_containers()
    except:
        raise HTTPException(status_code=500, detail=f"Error listing stopped containers")


@app.post("/stop_container", response_model=dict)
def container_stop(request: ContainerRequest):
    try:
        return stop_container(request.ContainerName)
    except:
        raise HTTPException(
            status_code=500, detail=f"Error stopping contianer {request.ContainerName}"
        )


@app.post("/get_logs/")
def get_logs_container(request: ContainerRequest):
    try:
        return get_logs(request.ContainerName)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@app.post("/start_container")
def start(request: ContainerRequest):
    try:
        return start_container(request.ContainerName)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@app.post("/container_details", response_model=dict)
def get_container_details(request: ContainerRequest):
    try:
        return container_details(request.ContainerName)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@app.post("/remove_container", response_model=dict)
def remove_container(request: RemoveContainerRequest):
    try:
        return container_remove(request.name, request.force, request.v)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error removing container: {str(e)}"
        )


@app.post("/build_image")
async def build_image(fileobj: UploadFile = File(...), obj: BuildImage = Depends()):
    try:
        return image_build(fileobj.file, obj.tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building image: {str(e)}")


# Database Routes


@app.get("/get_databases")
def get_databases():
    try:
        return mongo.get_databases()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting databases: {str(e)}"
        )


@app.get("/get_collections")
def get_collections():
    try:
        return mongo.get_collections()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting the collections: {str(e)}"
        )


@app.get("/get_collection_data")
def get_collection_data(request: CollectionName):
    try:
        data = mongo.get_collection_data(request.CollectionName)
        return {"data":data}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting collection data: {str(e)}"
        )
