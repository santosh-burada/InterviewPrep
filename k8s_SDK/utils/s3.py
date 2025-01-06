import boto3


class S3:
    def __init__(self, access_key: str, secret_key: str) -> None:
        self.s3_client = boto3.client(
            "s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key
        )

    def upload_file(self, img, key):
        try:
            self.s3_client.put_object(
                Body=img.file.read(), Bucket="k8s-compiler", Key=key
            )
            url = "https://k8s-compiler.s3.us-east-1.amazonaws.com/" + key
            return url
        except Exception as e:
            print(e.args)

    def delete_file(self, key):
        try:
            response = self.s3_client.delete_object(
                Bucket="k8s-compiler", Key=key
            )
            return response
        except Exception as e:
            print(e.args)
