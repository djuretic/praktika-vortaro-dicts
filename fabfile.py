from fabric.api import task
from fabric.operations import local

DOCKER_TAG='eo_dicts'

@task
def build_container():
    local("docker build . -t %s" % DOCKER_TAG)

def container_run(command):
    local("docker run --rm -v \"$(pwd):/src\" -it %s %s" % (DOCKER_TAG, command))

@task
def bash():
    container_run("bash")

@task
def test():
    container_run("pytest -vv")