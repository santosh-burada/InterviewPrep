import time
import base64
from kubernetes import client
import os
from utils.s3 import S3
from utils.logger_config import setup_logging

logging = setup_logging()

s3utils = S3(os.environ["access_key"], os.environ["secret_key"])

def create_namespace(namespace_name, v1):

    # Define the Namespace
    metadata = client.V1ObjectMeta(name=namespace_name)
    namespace = client.V1Namespace(metadata=metadata)

    # Create the Namespace
    try:
        v1.create_namespace(body=namespace)
        print(f"Namespace '{namespace_name}' created successfully.")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Namespace '{namespace_name}' already exists.")
        else:
            print(f"Error creating namespace: {e}")
            return None

    # Return the namespace name
    return namespace_name

def create_service(namespace, v1):
    # Define the Service
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name="dockersdk-service"),
        spec=client.V1ServiceSpec(
            selector={"app": "dockersdk"},  # Must match the app label in your deployment
            ports=[
                client.V1ServicePort(
                    protocol="TCP",
                    port=80,  # Target port inside the pod
                    target_port=80,
                    node_port=32000  # NodePort on the host
                )
            ],
            type="NodePort",  # Expose the service via NodePort
        )
    )

    # Create the Service
    try:
        v1.create_namespaced_service(namespace=namespace, body=service)
        print(f"Service 'dockersdk-service' created in namespace '{namespace}'.")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Service 'dockersdk-service' already exists in namespace '{namespace}'.")
        else:
            print(f"Error creating service: {e}")

def upload_to_s3(fileobj):
    try:
        path = s3utils.upload_file(fileobj, fileobj.filename)
        logging.info(f"Upload complete. Path: {path}")
        return {"path_to_object": path}
    except Exception as e:
        logging.exception("Error occurred during S3 upload")






