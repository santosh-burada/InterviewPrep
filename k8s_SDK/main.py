from kubernetes import client, config
from handlers import *
from fastapi import FastAPI, HTTPException, UploadFile, File
from job import job
from schemas import *
from db import MongoDB





app = FastAPI()
mongo = MongoDB(db_name="docker_sdk")
collection_name = mongo.create_collection("test_collection")

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
            status_code=500, detail=f"Error getting collection data: {str(e)}")

@app.post("/upload_s3_execute")
async def upload_s3_execute(fileobj: UploadFile = File(...)):

    try:
        local_path = f"/tmp/{fileobj.filename}"

        # Save file locally
        with open(local_path, "wb") as f:
            f.write(await fileobj.read())

        file_object = upload_to_s3(fileobj)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in upload_s3_execute: {str(e)}"
        )
    response = main()
    inserted_id = mongo.insert({"logs": response}, "test_collection")
    return {'job':response,"insertID": inserted_id}


def main():
    # Loading the local kubeconfig
    config.load_incluster_config()

    v1 = client.CoreV1Api()

    batch_v1 = client.BatchV1Api()
    response = batch_v1.create_namespaced_job(
        body=job,
        namespace="compiler"
    )

    return response.to_dict()


