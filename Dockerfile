# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# install conda
# see all versions available here: https://docs.conda.io/en/latest/miniconda_hashes.html
ENV PATH /opt/miniconda/bin:$PATH
RUN wget -qO /tmp/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -bf -p /opt/miniconda && \
    conda clean -ay && \
    rm -rf /opt/miniconda/pkgs && \
    rm /tmp/miniconda.sh && \
    find / -type d -name __pycache__ | xargs rm -rf

# init conda
RUN conda init bash

# update conda & pip
RUN conda update -n base -c defaults conda -y
RUN pip install --no-cache-dir --upgrade pip

# conda env setup from dependencies yaml file
COPY conda.yml /
RUN conda env update --name base -f conda.yml

# apply function specific requirements
COPY requirements.txt /
RUN pip install --no-cache-dir --use-feature=2020-resolver -r requirements.txt

# copy project code to site wwwroot
COPY . /home/site/wwwroot