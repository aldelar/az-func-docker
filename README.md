# az-func-docker

This repo demonstrates how to create a python Azure Function leveraging a runtime environment based on a custom docker container.

The function itself also connects to an Azure ML workspace Model registry to download at runtime an ML model and offer a scoring function as a web service. A Service Principal is used to establish the authentication to Azure ML as a Reader role.

This setup enables full control of the runtime environment and therefore the deployment of any type of ML model to Azure Functions as a PaaS ML endpoint.

The conda.yaml file is basically taken almost as is from the Azure ML service output directory of an Auto ML run.

# Setup Code

## Create Function code locally
func init az-func-docker --worker-runtime python --docker
func new --name score --template "HTTP trigger"

# Create Azure resources for deployment & deploy function

## Resource Group
az group create -n az-func-docker --location westus2

## Container Registry
az acr create -n azfuncdocker -g az-func-docker --sku Basic --admin-enabled true

## Storage Account
az storage account create -n azfuncdocker -g az-func-docker --location westus2 --sku Standard_LRS

## App Service Plan
az functionapp plan create -n azfuncdocker -g az-func-docker  --location westus2 --number-of-workers 1 --sku P1V2 --is-linux

## Azure Function
az functionapp create -n azfuncdocker -g az-func-docker --storage-account azfuncdocker --plan azfuncdocker --deployment-container-image-name azfuncdocker.azurecr.io/az-func-docker:latest --functions-version 3

## Enable Continuous deployment & Return CI_CD_URL
az functionapp deployment container config -n azfuncdocker -g az-func-docker --enable-cd --query CI_CD_URL --output tsv

## Copy the CI_CD_URL and set a new webhook in your Azure Container Registry (type 'Push')

## Enable Kudu/SSH connection to the container
Update the Dockerfile to use the '-appservice' version of the base image

Go to this URL to access the KUDU environment: https://az-func-docker.scm.azurewebsites.net/

# Azure ML Connectivity
## SEE: https://github.com/Azure/MachineLearningNotebooks/blob/master/how-to-use-azureml/manage-azureml-service/authentication-in-azureml/authentication-in-azureml.ipynb

## Create an app registration called 'azfuncdocker' from the Azure Active Directory resource

## Create a Secret named 'azfuncdocker' in this app using the Active Directory resource pane.

Copy the secret value before leaving the control pane. Save the value under "SERVICE_PRINCIPAL_PASSWORD" in local.settings.json

Copy the Tenant ID from the app overview pane into 'TENANT_ID' in local.settings.json

Copy the Application ID from the app overview pane into 'SERVICE_PRINCIPAL_ID' in local.settings.json

Setup your 'SUBSCRIPTION_ID' in the settings file.

Setup your Azure ML Workspace name and resource group under the 'AML_WORKSPACE_NAME' and 'AML_RESOURCE_GROUP' settings.

# Azure ML Workspace connectivity

Go to your Azure ML Workspace control pane in the Azure portal, and click on 'Access Control', then 'Add a role assignment':

Role: Reader
Select: azfuncdocker

Click Save. This provides the service principal the Reader role to your workspace so we can access the AML Model registry.

# Replicate the local.settings.json configuration in the Azure Function

Go to the Azure portal and open up the Azure Function.
Click on 'Configuration' and then create a new 'Application Setting' for each setting item created in the steps above. This should represent 6 new settings.

Click 'Save'.

NOTE: see 'local.settings.template.json' as a reference file. Your local.settings.json should look like this with filled in values for all the parameters defined coming from your Azure environment.

# Build and Test

# Login Docker desktop to your registry
docker login azfuncdocker.azurecr.io

You can find the username and password in the Azure portal registry panel, under 'Access Keys'.

## Build the docker image
make build

## Push the image to the Azure Registry, which will trigger a reboot of the Azure function against the new image
make push

## Test the image locally: Azure Function runtime
func start

## Test the image locally: Docker Desktop
make run-docker-local