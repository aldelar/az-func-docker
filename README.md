# az-func-docker

## Steps to rebuild this project

# Create Function code locally
func init az-func-docker --worker-runtime python --docker
func new --name score --template "HTTP trigger"

# Create Azure resources for deployment & deploy function
az group create --name az-func-docker --location westus2

az storage account create --name azfuncdocker --location westus2 --resource-group az-func-docker --sku Standard_LRS

az functionapp plan create --resource-group az-func-docker --name azfuncdocker --location westus2 --number-of-workers 1 --sku P1V2 --is-linux

az functionapp create --name az-func-docker --storage-account azfuncdocker --resource-group az-func-docker --plan azfuncdocker --deployment-container-image-name <myregistry>.azurecr.io/az-func-docker:latest --functions-version 3

az storage account show-connection-string --resource-group az-func-docker --name azfuncdocker --query connectionString --output tsv

az functionapp config appsettings set --name az-func-docker --resource-group az-func-docker --settings AzureWebJobsStorage="..(copy connection string from previous command).."

# Enable Continuous deployment & Return CI_CD_URL
az functionapp deployment container config --enable-cd --query CI_CD_URL --output tsv --name az-func-docker --resource-group az-func-docker

# copy the CI_CD_URL and set a new webhook in your Azure Container Registry (type 'Push')

# Enable Kudu/SSH connection to the container
# 1) Update the Dockerfile to use the '-appservice' version of the base image
# 2) Go to this URL to access the KUDU environment: https://az-func-docker.scm.azurewebsites.net/

# build the docker image
make build

# test the image locally
docker run -p 8080:80 -it ailabml1b51bd50.azurecr.io/az-func-docker:latest

# push the image to the Azure Registry, which will trigger a reboot of the Azure function against the new image
make push