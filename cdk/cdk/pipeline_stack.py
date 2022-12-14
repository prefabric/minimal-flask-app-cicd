from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_codedeploy as codedeploy,
    SecretValue,
)
from constructs import Construct

class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, common_infra_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        config = self.node.try_get_context("context")["config"]

        # CodePipeline pipeline creation
        pipeline = codepipeline.Pipeline(
            self,
            "cicd_pipeline",
            cross_account_keys=False,
            artifact_bucket=common_infra_stack.artifact_bucket,
        )

        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="Github_Source",
            output=source_output,
            owner=config["source"]["owner"],
            repo=config["source"]["repo"],
            oauth_token=SecretValue.secrets_manager(config["github_secret_name"]),
        )

        # Add source stage to pipeline
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Create CodeBuild project to build docker image
        repo_uri = common_infra_stack.ecr_repository.repository_uri
        app_name_lower = config['app_name'].lower()
        buildspec_commands = [
            f"docker build -t {app_name_lower}:$CODEBUILD_BUILD_NUMBER .",
            f"docker tag {app_name_lower}:$CODEBUILD_BUILD_NUMBER {repo_uri}:$CODEBUILD_BUILD_NUMBER",
            f"docker tag {app_name_lower}:$CODEBUILD_BUILD_NUMBER {repo_uri}:latest",
            "echo Pushing the Docker image...",
            f"docker push {repo_uri}:$CODEBUILD_BUILD_NUMBER",
            f"docker push {repo_uri}:latest",
            f'echo "export IMAGE_URI={repo_uri}:latest" > cdk/cdk/scripts/image_uri.sh'
        ]

        build_image_project = codebuild.PipelineProject(
            self,
            "BuildAppImageProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0,
                privileged=True,
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.10"
                        },
                        "commands": [
                            "echo Installing requirements...",
                            "make app_dependencies"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            "echo Logging in to Amazon ECR...",
                            f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.account}.dkr.ecr.{self.region}.amazonaws.com",
                            "echo Build started on `date`",
                            "echo Running app unit tests...",
                            "make app_test",
                            "echo Running linter...",
                            "make lint"
                        ]
                    },
                    "build": {
                        "commands": buildspec_commands,
                    },
                },
                "artifacts": {
                    "files": [
                        "docker-compose.yml",
                        "cdk/cdk/scripts/*",
                        "appspec.yml",
                    ]
                }
            }),
        )
        common_infra_stack.ecr_repository.grant_pull_push(build_image_project.role)

        build_output = codepipeline.Artifact()
        build_image_action = codepipeline_actions.CodeBuildAction(
            action_name="BuildImage",
            project=build_image_project,
            input=source_output,
            outputs=[build_output]
        )

        # Add build image stage to pipeline
        pipeline.add_stage(
            stage_name="BuildImage",
            actions=[build_image_action]
        )

        deployment_group = codedeploy.ServerDeploymentGroup(
            self,
            "FlaskAppDeploymentGroup",
            ec2_instance_tags=codedeploy.InstanceTagSet({
                "deploy_flask_app": ["true"],
            }),
            install_agent=False,
        )

        deploy_action = codepipeline_actions.CodeDeployServerDeployAction(
            action_name="CodeDeploy",
            input=build_output,
            deployment_group=deployment_group
        )
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_action]
        )
