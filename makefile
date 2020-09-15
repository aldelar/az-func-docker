# Define apps and registry
REGISTRY 		?=azfuncdocker.azurecr.io
IMAGE_NAME		?=az-func-docker
IMAGE_VERSION	?=latest

# Docker image build and push setting
DOCKER:=docker
DOCKERFILE:=Dockerfile

# build
.PHONY: build
build: build-image clean-dangling

.PHONY: build-image
build-image:
	$(DOCKER) build -f $(DOCKERFILE) . -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_VERSION)

# clean dangling
clean-dangling:
	$(eval DANGLING_IMAGES := $(shell docker images -f 'dangling=true' -q))
	$(if $(DANGLING_IMAGES),docker rmi --force $(DANGLING_IMAGES),)

# push
.PHONY: push
push:
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_VERSION)

# run-docker-local
.PHONY: run-docker-local
run-docker-local: build make-docker-env docker-local
make-docker-env:
	python generate_docker_env.py
docker-local:
	$(DOCKER) run -p 7071:80 -it --env-file local.settings.env $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_VERSION)