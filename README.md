# Seamless Integration of FPGA-based MPSoCs into Computing Continuum Infrastructures
This repository provides the open-source implementation, deployment environments, and custom configurations supporting the end-to-end design flow presented in the paper **"Seamless Integration of FPGA-based MPSoCs into Computing Continuum Infrastructures"**.
The framework enables the orchestration of acceleration-oriented containerized workloads (WLs) at the edge within a Computing Continuum (CC) environment, validating a custom Yocto-based Linux distribution against vendor alternatives.
The design flow has been fully validated on heterogeneous Edge Processing Systems (EPSs):
* **AMD Kria KV260 Vision Starter Kit** (Zynq UltraScale+ MPSoC, 64-bit ARMv8 Cortex-A53)
* **Digilent ZedBoard** (Zynq-7000 SoC, 32-bit ARMv7 Cortex-A9)

The core application utilized within the containerized workloads are based on:
- [AXI-based-driver-applications](https://github.com/mdc-suite/AXI-based-driver-applications) - Support for custom hardware kernels (AES, VPA).
- [VitisAI-based-applications](https://github.com/mdc-suite/VitisAI-based-applications) - Support for DPU inference models (Inception-v1, ResNet-50, YOLO-v3).

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
    └── axidma/
        └── yocto/
```

## FPGA-based WL Containerization
Inside each platform/OS subdirectory, the docker/ folder contains the building environment for containerizing workloads, linking hardware execution contexts:
* AI-oriented (Vitis AI): Integrates the .xmodel compilation artifacts with the Vitis AI Runtime (VART) libraries inside the image.
* Custom-HW (Vivado): Packages the hardware execution binaries interacting with the underlying AXI DMA drivers.

## Container Orchestration & FPGA Resource Exposure
The deployment folder contains the K3s deployment *.yaml* directives.
Hardware access is achieved by securely mapping the host architecture's device nodes directly into the pod specifications. The deployment YAMLs configure container privileges and volume mounts (e.g., /dev/xclmgmt*, /dev/dri* for Vitis AI DPU structures, or custom character devices for AXI DMA drivers). This allows the K3s worker node to forward raw hardware execution requests from inside the isolated container straight to the programmable logic fabric.


## Build example (Workload Containerization)
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

## Deployment example (K3s Orchestration)
To deploy the containerized workload onto your active K3s cluster, use the YAML file provided in the corresponding application directory.
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
