#!/usr/bin/env python3
import os

import aws_cdk as cdk
from dotenv import load_dotenv

from martin_stack.martin_stack import MartinStack

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), os.environ.get('ENV_FILE_PATH', '.cdk-stack-dev.env'))
)

ENV = cdk.Environment(region=os.environ.get('AWS_DEFAULT_REGION'), account=os.environ.get('AWS_ACCOUNT_ID'))
app = cdk.App()

MartinStack(app, os.environ.get('STACK_NAME'), env=ENV)
app.synth()
