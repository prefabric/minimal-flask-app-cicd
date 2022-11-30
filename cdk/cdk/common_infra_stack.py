import os

from aws_cdk import (
    Stack,
    aws_ecr as ecr,
    aws_s3_assets as s3_asset,
    aws_s3 as s3,
)
from constructs import Construct

dirname = os.path.dirname(__file__)

class CommonInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.ecr_repository = ecr.Repository(self, "app_image_repository")

        self.artifact_bucket = s3.Bucket(self, "artifact_bucket")

        self.nginx_conf = s3_asset.Asset(
            self,
            'NginxConf',
            path=os.path.join(dirname, 'scripts/nginx.conf')
        )
