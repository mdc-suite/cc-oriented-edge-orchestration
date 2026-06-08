# K3s deployment for AXI DMA and Vitis AI Applications
This flow has been validated for AMD FPGA-based MPSoC platforms (Zynq UltraScale+ and Zynq-7000 families) for which dedicated Yocto layers are available (such as AMD Kria KV260 and Digilent Zedboard).

This repository provides a structured collection of deployment environments for applications based on:

- [AXI-based-driver-applications](https://github.com/mdc-suite/AXI-based-driver-applications)

- [VitisAI-based-applications](https://github.com/mdc-suite/VitisAI-based-applications)

## Repository Structure
The repository is organized by application family and operating system.
```text
├── axidma
│   ├── ubuntu
│   └── yocto
└── vitis-AI
    ├── ubuntu
    ├── yocto
    └── petalinux
```
Each OS-specific directory includes:

- A Docker build context for creating the required container image

- YAML deployment files for the corresponding operating system
```text
<application>/
└── <os>/
    ├── docker/
    └── *.yaml
```

## Build example
To build the container image for an ARM target, move into the docker directory of the selected application and operating system, then use Docker Buildx.
```bash
cd axidma/ubuntu/docker
docker buildx build --platform linux/arm64 -t <username>/<image-name>:<tag> --push .
```
Replace:
- <username> with your Dockerhub username
- <image-name> with the desired image name
- <tag> with the image tag to assign

## Deployment example
To deploy the container on a k3s cluster, use the YAML file provided in the corresponding OS directory.
```bash
cd axidma/ubuntu
kubectl apply -f <deployment-file>.yaml
```
Replace <deployment-file>.yaml with the actual YAML file name.

To verify that the deployment has been created successfully, run:
```bash
kubectl get pods
kubectl logs <pod-name>
```

