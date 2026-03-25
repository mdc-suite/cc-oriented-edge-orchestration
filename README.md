# K3s deployment for AXI DMA and Vitis AI Applications on KV260
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
