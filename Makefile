BUILD_NUMBER?=0

DOCKER_MAKE?=true


define run_sh_cmd
	$(1)
endef


ifndef JENKINS_HOME
define docker_vars
	-it
endef
else
define docker_vars
endef
endif


define run_docker_cmd
	docker run --rm \
		$(docker_vars) \
		-v `pwd`:/app \
		-e BUILD_NUMBER=$(BUILD_NUMBER) \
		-e PIPENV_SHELL=/bin/bash \
		granular_configuration \
		bash -c "$(1)"
endef


define run_cmd
	$(if $(filter $(DOCKER_MAKE),true), $(call run_docker_cmd,$(1)), $(call run_sh_cmd,$(1)))
endef


.PHONY: build bump_major bump_minor bump_patch clean dev lock package test


all:
	@echo 'Commands:'
	@echo ''
	@echo 'build - build the docker container'
	@echo 'bump_major - bump the major version of the project'
	@echo 'bump_minor - bump the minor version of the project'
	@echo 'bump_patch - bump the patch version of the project'
	@echo 'clean - clean the build and test files'
	@echo 'dev - install the dev dependencies and start a pipenv shell'
	@echo 'lock - update the pipenv lock file'
	@echo 'package - build the pip package'
	@echo 'test - run the tests and linting'

bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

bump_major:
	bumpversion major

build38:
	$(if $(filter $(DOCKER_MAKE),true), docker build -f Dockerfile3.8 -t granular_configuration .,:)

build37:
	$(if $(filter $(DOCKER_MAKE),true), docker build -f Dockerfile3.7 -t granular_configuration .,:)

build36:
	$(if $(filter $(DOCKER_MAKE),true), docker build -f Dockerfile3.6 -t granular_configuration .,:)

test36: build36
	@echo "--------------------------------------------------------------------------------"
	@echo "running tests on Python 3.6"
	@echo "--------------------------------------------------------------------------------"
	$(call run_cmd,pipenv run tools/unit_test)

test37: build37
	@echo "--------------------------------------------------------------------------------"
	@echo "running tests on Python 3.7"
	@echo "--------------------------------------------------------------------------------"
	$(call run_cmd,pipenv run tools/unit_test)

test38: build38
	@echo "--------------------------------------------------------------------------------"
	@echo "running tests on Python 3.8"
	@echo "--------------------------------------------------------------------------------"
	$(call run_cmd,pipenv run tools/unit_test)

test: test36 test37 test38
	@echo "--------------------------------------------------------------------------------"
	@echo "Ran tests on all Pythons"
	@echo "--------------------------------------------------------------------------------"

dev: build37
	$(call run_cmd,pipenv shell)

lock: build37
	@echo "--------------------------------------------------------------------------------"
	@echo "updating pipenv lock file"
	@echo "--------------------------------------------------------------------------------"
	$(call run_cmd,pipenv lock)

package: build37
	@echo "--------------------------------------------------------------------------------"
	@echo "building package"
	@echo "--------------------------------------------------------------------------------"
	$(call run_cmd,pipenv run tools/package)

clean:
	rm -rf build
	rm -rf dist
	rm -rf results
	rm -rf granular_configuration.egg-info
