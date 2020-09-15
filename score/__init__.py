import json
import logging
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.externals import joblib

import azureml.automl.core
from azureml.telemetry import INSTRUMENTATION_KEY

from inference_schema.schema_decorators import input_schema, output_schema
from inference_schema.parameter_types.numpy_parameter_type import NumpyParameterType
from inference_schema.parameter_types.pandas_parameter_type import PandasParameterType

import azure.functions as func

# Python platform check
import platform

# Service Principal Authentication
from azureml.core.authentication import ServicePrincipalAuthentication
svc_pr = ServicePrincipalAuthentication(
    tenant_id=os.environ['TENANT_ID'],
    service_principal_id=os.environ['SERVICE_PRINCIPAL_ID'], # aka Application (client) ID in AD app
    service_principal_password=os.environ['SERVICE_PRINCIPAL_PASSWORD']) # aka Secret value created in AD app
# AzureML Workspace
from azureml.core import Workspace, Model
workspace = Workspace(
    subscription_id=os.environ['SUBSCRIPTION_ID'],
    resource_group=os.environ['AML_RESOURCE_GROUP'],
    workspace_name=os.environ['AML_WORKSPACE_NAME'],
    auth=svc_pr)

# list of models loaded in memory
models = {}

#
input_sample = pd.DataFrame({"trade_date": pd.Series(["2020-09-01T00:00:00.000Z"], dtype="datetime64[ns]")})
#@input_schema('data', PandasParameterType(input_sample, enforce_shape=False))
def main(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info('Python HTTP trigger function processed a request.')
    # log python architecture version
    logging.info(platform.architecture())

    # get params
    model_name = read_param(req,'model_name','')
    model_version = read_param(req,'model_version',1)
    
    # get model
    model = get_model(model_name,model_version)
    logging.info(f"req.body: {json.loads(req.get_body())}")

    # score the model
    try:
        y_query = None
        data = PandasParameterType(input_sample, enforce_shape=False)
        #if 'y_query' in data.columns:
        #    y_query = data.pop('y_query').values
        result = model.forecast(input_sample, y_query)
    except Exception as e:
        result = str(e)
        return json.dumps({"error": result})

    # format response
    forecast_as_list = result[0].tolist()
    index_as_df = result[1].index.to_frame().reset_index(drop=True)
    response = json.dumps({"forecast": forecast_as_list,"index": json.loads(index_as_df.to_json(orient='records'))})
    
    # return response
    return func.HttpResponse(
        body=response,
        mimetype="application/json",
        status_code=200
    )

# read param from query params or body
def read_param(req,param_name,param_default):
    param_value = req.params.get(param_name)
    if not param_value:
        try:
            req_body = req.get_json()
        except ValueError:
            param_value = param_default
        else:
            param_value = req_body.get(param_name)
    return param_value

# get model
def get_model(model_name,model_version):
    logging.info(f'get_model({model_name,model_version})')
    if not model_version in models:
        models[model_version] = load_model_from_registry(model_name,model_version)
    return models[model_version]

# load_model_from_registry
def load_model_from_registry(model_name,model_version):
    logging.info(f' >> load_model_from_registry({model_name},{model_version}) ...')
    try:
        aml_model = Model(workspace, name=model_name, version=model_version)
        model_path = aml_model.download(target_dir='.',exist_ok=True)
        return joblib.load(model_path)
    except Exception as e:
        logging.error(e)
        raise