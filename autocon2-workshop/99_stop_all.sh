#!/bin/bash
#stop all the stuff
#
pushd slurpit
docker compose down
popd

pushd network
sudo clab destroy
popd

pushd netbox-docker
docker compose down
popd

pushd icinga2-docker-stack
docker compose down
popd

pushd netpicker
docker compose down
popd
