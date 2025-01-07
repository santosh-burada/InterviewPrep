from kubernetes import client
import uuid


# Define the job specification
job = client.V1Job(
    api_version="batch/v1",
    kind="Job",
    metadata=client.V1ObjectMeta(name=f"compiler-{str(uuid.uuid1())[:10]}", namespace="compiler"),
    spec=client.V1JobSpec(
        # ttl_seconds_after_finished=100,
        template=client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                # service_account_name="compiler-service-account",
                volumes=[
                    client.V1Volume(
                        name="code-volume",
                        empty_dir=client.V1EmptyDirVolumeSource()
                    )
                ],
                init_containers=[
                    client.V1Container(
                        name="code-download",
                        image="amazon/aws-cli",
                        args=["s3", "cp", "$(FILE_PATH)", "/code/$(FILE_NAME)"],
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/code",
                                name="code-volume"
                            )
                        ],
                        env = [
                            client.V1EnvVar(
                                name= "AWS_ACCESS_KEY_ID",
                                value_from=client.V1EnvVarSource(
                                    secret_key_ref = client.V1SecretKeySelector(
                                        name="aws-credentials",
                                        key="access_key"
                                    )
                                )
                            ),

                            client.V1EnvVar(
                                name="AWS_SECRET_ACCESS_KEY",
                                value_from=client.V1EnvVarSource(
                                    secret_key_ref=client.V1SecretKeySelector(
                                         name="aws-credentials",
                                         key="secret_key"
                                    )
                                )
                            ),
                            client.V1EnvVar(
                                name = "FILE_PATH",
                                value="s3://k8s-compiler/test.py"
                            ),
                            client.V1EnvVar(
                                name="FILE_NAME",
                                value="test.py"
                            )
                        ]
                    )
                ],
                containers=[
                    client.V1Container(
                        name="compiler",
                        image="santoshburada/runner:v1.0",
                        image_pull_policy="IfNotPresent",
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/code",
                                name="code-volume"
                            )
                        ],
                        env=[
                            client.V1EnvVar(
                                name="FILE_NAME",
                                value="test.py"
                            )
                        ],
                        command=["python", "/app/run.py"],
                        args=["/code/$(FILE_NAME)"]
                    )
                ],
                restart_policy="Never"
                
            )
        )
    )
)

