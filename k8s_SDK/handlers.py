import time
import base64
from kubernetes import client
import os
from utils.s3 import S3
from utils.logger_config import setup_logging

logging = setup_logging()

s3utils = S3(os.environ["access_key"], os.environ["secret_key"])

# def create_deployment_object():
#     env_vars = [
#         client.V1EnvVar(
#             name="access_key",
#             value_from=client.V1EnvVarSource(
#                 secret_key_ref=client.V1SecretKeySelector(
#                     name="access-secret",
#                     key="access_key"
#                 )
#             )
#         ),
#         client.V1EnvVar(
#             name="secret_key",
#             value_from=client.V1EnvVarSource(
#                 secret_key_ref=client.V1SecretKeySelector(
#                     name="access-secret",
#                     key="secret_key"
#                 )
#             )
#         )
#     ]
#     container = client.V1Container(
#         name="dockersdk",
#         image="santoshburada/docker_sdk:v1.0",
#         image_pull_policy="IfNotPresent",
#         ports=[client.V1ContainerPort(container_port=80)],
#         env=env_vars
#     )
#     # Template
#     template = client.V1PodTemplateSpec(
#         metadata=client.V1ObjectMeta(labels={"app": "dockersdk"}),
#         spec=client.V1PodSpec(containers=[container]))
#     # Spec
#     spec = client.V1DeploymentSpec(
#         replicas=1,
#         selector=client.V1LabelSelector(
#             match_labels={"app": "dockersdk"}
#         ),
#         template=template)
#     # Deployment
#     deployment = client.V1Deployment(
#         api_version="apps/v1",
#         kind="Deployment",
#         metadata=client.V1ObjectMeta(name="deploy-dockersdk"),
#         spec=spec)

#     return deployment

# def create_deployment(apps_v1_api, deployment_object, namespace):
#     # Create the Deployment in default namespace
#     # You can replace the namespace with you have created
#     apps_v1_api.create_namespaced_deployment(
#         namespace=namespace, body=deployment_object
#     )

def create_secret(namespace, v1):
    metadata = client.V1ObjectMeta(name="access-secret")
    data = {
        "access_key": base64.b64encode("AKIAVRUVU5U4V63OSYGT".encode()).decode(),  # Replace with your access key
        "secret_key": base64.b64encode("M6MiBCo7G1vEkq5ihq8hIdG5b5vtTR7I544eZGbU".encode()).decode()  # Replace with your secret key
    }
  
    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=metadata,
        type="Opaque",
        data=data,
    )
    try:
        v1.create_namespaced_secret(namespace=namespace, body=secret)
        print(f"Secret 'access-secret' created in namespace '{namespace}'.")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Secret 'access-secret' already exists in namespace '{namespace}'.")
        else:
            print(f"Error creating secret: {e}")

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






