import os

import aws_cdk as cdk

from cdk.pipeline_stack import PipelineStack
from cdk.common_infra_stack import CommonInfraStack
from cdk.prod_stack import ProdStack


app = cdk.App()

env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))

common_infra_stack = CommonInfraStack(app, "CommonInfraStack", env=env)
prod_stack = ProdStack(app, "ProdStack", env=env, common_infra_stack=common_infra_stack)
prod_stack.add_dependency(common_infra_stack)

pipeline_stack = PipelineStack(
    app,
    "PipelineStack",
    common_infra_stack=common_infra_stack,
    env=env,
)
pipeline_stack.add_dependency(common_infra_stack)
pipeline_stack.add_dependency(prod_stack)

app.synth()
