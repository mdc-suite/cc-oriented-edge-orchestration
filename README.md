# Seamless Integration of FPGA-based MPSoCs into Computing Continuum Infrastructures
This repository provides the open-source implementation, deployment environments, and custom configurations supporting the end-to-end design flow.
The framework enables the orchestration of acceleration-oriented containerized workloads (WLs) at the edge within a Computing Continuum (CC) environment, validating a custom Yocto-based Linux distribution against vendor alternatives.
The design flow has been fully validated on heterogeneous edge devices:
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
The K3s orchestration layer manages and deploys containerized workloads across edge nodes by securely mapping the host's underlying hardware interfaces and device nodes directly into the pod specifications. To allow user-space applications to communicate with the programmable logic without virtualization overhead, workloads are executed with administrative privileges (`privileged: true`) combined with explicit `hostPath` volume mounts.

### 1. AI-oriented workloads
For deep learning pipelines (Inception-v1, ResNet-50, YOLO-v3), hardware exposure is achieved by mounting key system and rendering device paths:
* **/dev/dri**: Maps the Direct Rendering Infrastructure, allowing user-space libraries (VART) to interact with the DPU character devices.
* **/var/run/dfx-mgrd.socket**: Forwards the Unix socket of the Xilinx Dynamic Function eXchange daemon (`dfx-mgrd`) to enable secure runtime hardware management inside the container.
* **/lib/firmware/xilinx**: Exposes the host directory containing platform-specific DPU configuration assets and firmware overlays.

### 2. Custom-HW workloads
For algorithmic kernels (AES, VPA), the orchestrator exposes the low-level configuration and driver paths to manage dynamic hardware reprogramming and communication:
* **/dev/fpga0** & **/dev/axidma**: Grant direct access to the FPGA manager interfaces and hardware-centric Direct Memory Access modules.
* **/dev** (mounted as `/host-dev`): Allows the container to monitor the host subsystem and access dynamically generated character device nodes.
* **/dev/uniss_dma**: The specific character device created on the host after the bitstream and driver are dynamically inserted.
* **/sys** & **/sys/kernel/config** (`configfs`): Required by the container runtime to interact with the Linux kernel subsystem for dynamic hardware loading.
* **/lib/firmware**: Provides access to the system directory containing the custom bitstream binaries (`.bit`/`.bin`) and device tree overlays (`.dtbo`).


## Build example (Workload Containerization)
To build the container image for an ARM target, move into the docker directory of the selected application and platform, then use Docker Buildx.
```bash
cd kv260/axidma/<os>/<app>/docker-<app>
docker buildx build --platform linux/arm64 -t <username>/<image-name>:<tag> --push .

cd zedboard/axidma/yocto/<app>/docker-<app>
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
