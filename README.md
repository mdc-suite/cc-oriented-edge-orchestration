# K3s deployment for AXI DMA and Vitis AI Applications

This flow has been validated for AMD FPGA-based MPSoC platforms (Zynq UltraScale+ and Zynq-7000 families) for which dedicated Yocto layers are available (such as AMD Kria KV260 and Digilent Zedboard).

This repository provides a structured collection of deployment environments for applications based on:

- [AXI-based-driver-applications](https://github.com/mdc-suite/AXI-based-driver-applications)
- [VitisAI-based-applications](https://github.com/mdc-suite/VitisAI-based-applications)

## Repository Structure

The repository is organized primarily by target hardware platforms, and sub-divided by application family or deployment environment:

```text
├── kv260/
│   ├── axidma/
│       ├── ubuntu
│       └── yocto
│   └── vitis-AI/
│       ├── ubuntu
│       ├── yocto
│       └── petalinux
└── zedboard/
│   └── axidma/
│       └── yocto/
```

## Inner Directory Structure
Inside each application/OS directory (e.g., kv260/axidma/ or zedboard/axidma/yocto/), the content is structured to support containerized orchestration:

* docker/: Contains the Docker build context for creating the required container image for the target architecture.
* *.yaml files: Kubernetes/K3s deployment files tailored for the corresponding operating system and hardware configuration.

## Build example
To build the container image for an ARM target, move into the docker directory of the selected application and platform, then use Docker Buildx.
```bash
cd kv260/axidma/<os>/<app>/docker-<app>
docker buildx build --platform linux/arm64 -t <username>/<image-name>:<tag> --push .

cd zedboard/axidma/yocto//<app>/docker-<app>
docker buildx build --platform linux/arm/v7 -t <username>/<image-name>:<tag> --push .

```
Replace:
* <username> with your Dockerhub username
* <image-name> with the desired image name
* <tag> with the image tag to assign

## Deployment example
To deploy the container on a k3s cluster, use the YAML file provided in the corresponding application directory.
```bash
cd kv260/axidma/<os>/<app>
kubectl apply -f <deployment-file>.yaml
```
Replace <deployment-file>.yaml with the actual YAML file name.

To verify that the deployment has been created successfully, run:
```bash
kubectl get pods
kubectl logs <pod-name>
```
