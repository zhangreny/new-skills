---
title: "everoute/3.5.0/Everoute 安装与升级指南"
source_url: "https://internal-docs.smartx.com/everoute/3.5.0/er_installation_guide/installation_guide_preface-generic"
sections: 26
---

# everoute/3.5.0/Everoute 安装与升级指南
## 关于本文档

# 部署 Everoute 服务

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**。
2. 在弹出的页面左侧位置单击 **+ 部署 Everoute 服务**，进入配置信息页面。
3. 根据页面提示按需完成[基本信息](/everoute/3.5.0/er_installation_guide/installation_guide_13)、[Everoute Controller](/everoute/3.5.0/er_installation_guide/installation_guide_14)、[分布式防火墙](/everoute/3.5.0/er_installation_guide/installation_guide_15)、[虚拟专有云网络](/everoute/3.5.0/er_installation_guide/installation_guide_35)和[网络负载均衡器](/everoute/3.5.0/er_installation_guide/installation_guide_16)配置。
4. 完成配置后，单击**部署**，系统将自动在集群上完成 Everoute 服务的部署。

   > **注意**：
   >
   > Everoute 服务使用 CloudTower 的 NTP 服务器进行时间同步，部署完成后请参考《CloudTower 使用指南》的**配置 NTP 服务器**章节，确保 CloudTower 中已正确配置了 NTP 服务器，以免影响 Everoute 服务的正常运行。

---

## 文档更新信息

# 文档更新信息

**2026-01-30：配合 Everoute 3.5.0 正式发布**

相较于 Everoute 3.4.1，本版本主要更新了以下内容：

- **概述**：新增网络安全导流功能的介绍。
- **部署前的准备**：
  - **规划 IP 地址**：新增网络安全导流功能需规划的 IP 地址说明；补充说明 Everoute Controller 仲裁节点可复用 CloudTower 高可用仲裁节点的 IP。
  - **规划端口**：新增网络安全导流功能的端口开放说明；删除源端为 CloudTower 虚拟机、目标端为关联的集群中的主机时，目标端需开放 80 端口的要求。
  - **规划 Everoute Controller**：更新每种配置类型可管理的功能；新增不同 Everoute Controller 配置类型可管理的虚拟服务资源的数量说明。
- **安装部署 Everoute** > **部署 Everoute 服务**：
  - **配置基本信息**：新增支持网络安全导流功能。
  - **配置 Everoute Controller**：新增 Everoute Controller 仲裁节点复用 CloudTower 高可用仲裁节点的说明。
- **升级 Everoute 服务**：新增 Everoute Controller 仲裁节点复用 CloudTower 高可用仲裁节点的说明。

---

## 概述

# 概述

Everoute 是由北京志凌海纳科技股份有限公司（以下简称 “SmartX”）自主研发的网络与安全产品，为 SmartX 超融合和企业云基础设施提供了软件定义的网络和安全系列功能。Everoute 可提供分布式防火墙、网络安全导流、虚拟专有云网络、负载均衡、容器网络等功能，同时支撑虚拟化和容器化应用，从而形成与虚拟机和容器一体化管理的网络和安全解决方案。

- **分布式防火墙**

  Everoute 分布式防火墙（Distributed firewall）基于 SmartX 原生虚拟化 ELF，结合虚拟分布式交换机实现了符合“零信任”要求的微分段网络模型，可为虚拟机提供虚拟机隔离、自定义安全策略、全局安全策略三种形态的分布式防火墙策略。Everoute 分布式防火墙解决了数据中心虚拟网络安全面临的挑战，为业务提供更加灵活精细的网络安全保障。
- **虚拟专有云网络**

  Everoute 虚拟专有云网络（ Virtual Private Cloud，VPC） 是 SmartX 的虚拟化网络产品，可以在 SmartX 企业云环境中为虚拟机提供安全隔离的网络空间，并通过虚拟化网络功能（VNF）实现虚拟网络内部和外部的安全互联互通，使用户可以更加快速灵活地在多个数据中心部署统一的企业云网络。
- **网络负载均衡器**

  Everoute 负载均衡（Load Balancer，LB），作为 Everoute 网络与安全产品的功能，部署在 SmartX 虚拟化 ELF 平台的集群中，可为基于虚拟机、容器或物理服务器的应用提供负载均衡服务。
- **网络安全导流**

  Everoute 网络安全导流（Security traffic steering）可支持在 SmartX 原生虚拟化 ELF 中，将特定虚拟分布式交换机中的出入网络流量导流至特定的安全服务设备，以实现对网络流量的深度检测、入侵防御、防火墙等能力，保证虚拟机中的网络数据安全。

---

## 概述 > 产品特性

# 产品特性

Everoute 产品具有如下特性：

- **易使用**

  - 无需安装任何插件。
  - 采用声明式 API，通过代码的方式实现安全即代码（SaaC: Security as a Code），您只需要关注期望结果而无需关心中间过程。
  - 提供友好的图形化界面，实现灵活易用的配置管理。
  - 无需调整物理网络上的交换、路由、安全等配置。
  - 提供丰富的网关，通过简单的界面操作即可连通虚拟专有云网络与外部网络。
- **可扩展**

  - 采用分布式架构，具备横向扩展性，也支持控制节点纵向扩容。
  - 支持跨数据中心的统一安全策略及虚拟服务管理。
- **高可用**

  - 多控制器实例组成高可用集群，无单点故障。
  - 控制与转发分离，控制平面故障不影响网络数据转发。
- **广泛兼容**

  - 支持任意底层网络架构，无物理网络设备品牌、型号和功能依赖。
  - 纯软件实现方案，无硬件设备（如网卡、服务器）依赖。
  - 支持 Intel x86\_64、Hygon x86\_64、鲲鹏 AArch64、飞腾 AArch64 多种架构平台混合部署和使用。
- **高安全性**

  虚拟专有云网络通过 GENEVE 隧道提供完全逻辑隔离的网络环境，不同 VPC 之间、VPC 与物理网络之间默认不能通信，并且提供安全组、安全策略等功能，对 VPC 内的虚拟机资源进行防护。

---

## 概述 > 产品架构

# 产品架构

Everoute 由管理平面、控制平面和数据平面组成。

- **管理平面**

  管理平面主要由 Everoute operator、Web UI 和 API 组成。用户通过 CloudTower 或 API 访问 Everoute Operator，可以对 Everoute 进行部署、扩容、开启分布式防火墙功能、开启网络负载均衡器功能等操作。
- **控制平面**

  控制平面由 1 个、3 个或 5 个部署在 SMTX OS（ELF）集群或 SMTX ELF 集群的 Everoute Controller 组成，分布式防火墙功能、虚拟专有云网络功能、网络负载均衡器功能和网络安全导流功能的控制平面组件共享 Everoute Controller 的存储计算资源，负责为数据平面生成转发规则。
- **数据平面**

  数据平面分为三部分，分布式防火墙及网络安全导流、虚拟专有云网络和网络负载均衡器。

  - **分布式防火墙及网络安全导流**的数据平面部署到被关联的 SMTX OS（ELF）集群或 SMTX ELF 集群上，负责为集群上的虚拟机执行数据转发规则，控制虚拟机数据流量的转发、实现虚拟机隔离等。
  - **虚拟专有云网络**的数据平面部署到被关联的 SMTX OS（ELF）集群或 SMTX ELF 集群上，通过集群中的虚拟分布式交换机上特定的虚拟网络转发规则，控制虚拟专有云网络中特定虚拟机间的数据通信、流量转发以及虚拟机隔离。
  - **网络负载均衡器**的数据平面部署在一组或多组虚拟机内，负责生成负载均衡规则，将客户端流量转发到后端服务器上，同时完成负载均衡相关的健康检查、会话保持、流量控制、访问控制等功能。

Everoute 各功能架构的详细介绍，请参考[《Everoute 分布式防火墙技术白皮书》](/everoute/3.5.0/er_whitepaper/whitepaper_preface_generic)、[《Everoute 虚拟专有云网络技术白皮书》](/everoute/3.5.0/er_whitepaper_vpc/whitepaper_vpc_preface-generic)和[《Everoute 网络负载均衡器技术白皮书》](/everoute/3.5.0/er_whitepaper_lb/whitepaper_lb_preface-generic)。

---

## 部署前的准备

# 部署前的准备

部署 Everoute 服务前，请确认版本配套要求、下载安装文件，并根据需要启用的功能规划 Everoute Controller、防火墙端口、IP 地址、LB 虚拟机、虚拟专有云网络等。

---

## 部署前的准备 > 确认版本配套要求

# 确认版本配套要求

在部署前请参考《Everoute 发布说明》的[版本配套说明](/everoute/3.5.0/er_release_notes/release_notes_02)，确认 SMTX OS（ELF）集群或 SMTX ELF 集群版本以及 CloudTower 版本满足要求。

---

## 部署前的准备 > 获取安装文件

# 获取安装文件

在部署前请您提前获取 Everoute 的安装文件。

---

## 部署前的准备 > 规划 IP 地址

# 规划 IP 地址

部署前，请先从网络管理员处获取如下 IP 地址：

| IP 地址 | 分布式防火墙 | 虚拟专有云网络 | 网络负载均衡器 | 网络安全导流 |
| --- | --- | --- | --- | --- |
| 每个 Everoute Controller 工作节点的管理 IP 地址及其子网掩码、网关信息；如使用 Everoute Controller 仲裁节点，则将直接复用双活集群仲裁节点的管理 IP 或 CloudTower 高可用仲裁节点的 IP 地址，无需单独配置 | ✓ | ✓ | ✓ | ✓ |
| 每个 LB 虚拟机的管理 IP 地址及其子网掩码、网关信息；每个 LB 虚拟机的 TEP IP 地址（LB 支持 VPC 时使用） |  |  | ✓ |  |
| 内部服务子网的 CIDR 块 |  | ✓ |  |  |
| 每个 TEP IP 池的起始 IP、结束 IP 及其子网掩码、网关信息 |  | ✓ |  |  |
| 每个边缘网关虚拟机的管理 IP 地址及其子网掩码、网关信息；每个边缘网关虚拟机的 TEP IP 地址 |  | ✓ |  |  |
| 外部子网的 CIDR 块及其网关信息 |  | ✓ |  |  |

网络管理员在分配 IP 地址时，必须遵循以下规则：

- Everoute Controller 仲裁节点与工作节点的管理 IP 地址连通，工作节点之间的管理 IP 地址相互连通，且均与 CloudTower 的 IP 地址连通。

  - 如需使用分布式防火墙功能，还须与其计划要关联的集群中的每台主机的管理 IP 地址连通。
  - 如需使用虚拟专有云网络功能，还须与其计划要关联的集群中的每台主机的管理 IP 地址、每台边缘网关虚拟机的管理 IP 地址连通。
  - 如需使用网络负载均衡器功能，还须与 LB 实例或 LB 实例组中的每台 LB 虚拟机的管理 IP 地址连通。
- 同一个 LB 实例或 LB 实例组中，所有 LB 虚拟机的管理 IP 地址之间必须能够连通。
- 同一个边缘网关或边缘网关组中，所有边缘网关虚拟机的管理 IP 地址之间必须能够连通。
- TEP IP 和内部服务子网的规划请参考[虚拟专有云网络规划](/everoute/3.5.0/er_installation_guide/installation_guide_36)。
- IP 地址不能与以下 CIDR 范围内的任何 IP 地址重叠：

  - 169.254.0.0/16
  - 240.0.0.0/4
  - 224.0.0.0/4
  - 198.18.0.0/15
  - 127.0.0.0/8
  - 0.0.0.0/8

---

## 部署前的准备 > 规划端口

# 规划端口

为了确保 Everoute 服务的正常进行，当源端访问目标端时，目标端需要开放相应的端口，请您根据所使用的功能查看需开放的端口及端口说明。下列端口如没有特殊说明，均表示端口的传输端协议为 TCP。

## 分布式防火墙

| 源端 | 目标端 | 目标端需开放的端口 | 端口说明 |
| --- | --- | --- | --- |
| CloudTower 虚拟机 | Everoute Controller 工作节点 | 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 中的组件。 |
| Everoute Controller 工作节点 | Everoute Controller 工作节点 | 2379 | 扩容时， Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| 关联的集群中的主机 | Everoute Controller 工作节点 | 6443 | 关联的集群中的主机通过该端口同步安全策略资源。 |
| CloudTower 虚拟机 | 关联的集群中的主机 | 8500 | 在将 SMTX OS（ELF）集群或 SMTX ELF 集群和 Everoute 进行关联时， CloudTower 虚拟机通过该端口注册 Everoute Controller 服务。 |
| 10000 | CloudTower 虚拟机通过该端口完成 Everoute agent 的部署和升级。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |
| Everoute Controller 工作节点 | CloudTower 虚拟机 | 443 | Everoute agent 通过该端口从 CloudTower 同步标签、安全策略、虚拟机信息。 |
| Everoute Controller 工作节点 | Everoute Controller 仲裁节点 | 30000 | Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 30001 | Everoute Controller 工作节点和仲裁节点之间通过该端⼝同步 Everoute 的存储数据。 |
| Everoute Controller 仲裁节点 | Everoute Controller 工作节点 | 2379 | Everoute Controller 仲裁节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 仲裁节点和工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| CloudTower 虚拟机 | Everoute Controller 仲裁节点 | 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 仲裁节点中的 Everoute 组件。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |
| Everoute Controller 虚拟机 | SKS 管控集群和工作负载集群的 Control Plane 节点对应的虚拟机及 Control Plane 虚拟 IP | 6443 | Everoute Controller 虚拟机通过该端口为 Pod 配置安全策略，同步 Pod 信息。 |

## 虚拟专有云网络

| 源端 | 目标端 | 目标端需开放的端口 | 端口说明 |
| --- | --- | --- | --- |
| CloudTower 虚拟机 | Everoute Controller 工作节点 | 6445 | 虚拟专有云网络对外暴露 API， CloudTower 虚拟机通过该端口完成 API 调用。 |
| 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 中的组件。 |
| Everoute Controller 工作节点 | Everoute Controller 工作节点 | 2379 | 扩容时， Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| 关联的集群中的主机 | Everoute Controller 工作节点 | 6443 | 关联的集群中的主机通过该端口同步虚拟专有云网络资源。 |
| 6445 | 关联的集群中的主机通过该端口同步虚拟专有云网络资源。 |
| 边缘网关虚拟机 | Everoute Controller 工作节点 | 6443 | 网关虚拟机通过该端口同步虚拟专有云网络相关资源。 |
| CloudTower 虚拟机 | 关联的集群中的主机 | 8500 | 在将 SMTX OS（ELF）集群或 SMTX ELF 集群和 Everoute 进行关联时， CloudTower 虚拟机通过该端口注册 Everoute Controller 服务。 |
| 10000 | CloudTower 虚拟机通过该端口完成 Everoute agent 的部署和升级。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 边缘网关虚拟机、支持 VPC 的 LB 虚拟机、关联的集群中的主机 | 边缘网关虚拟机、支持 VPC 的 LB 虚拟机、关联的集群中的主机 | ICMP | TEP IP 之间通过该端口进行健康检查。 |
| 6081（UDP） | GENEVE 隧道报文通信端口。 |
| Everoute Controller 工作节点 | CloudTower 虚拟机 | 443 | Everoute agent 通过该端口从 CloudTower 同步标签信息。 |
| 边缘网关虚拟机 | 边缘网关虚拟机 | 10100（UDP） | 网关虚拟机之间通过该端口检测高可用心跳。 |
| 10101（UDP） | 网关虚拟机之间通过该端口同步 conntrackd 会话。 |
| CloudTower 虚拟机 | 边缘网关虚拟机 | 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级边缘网关虚拟机中的组件。 |
| Everoute Controller 工作节点 | Everoute Controller 仲裁节点 | 30000 | Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 30001 | Everoute Controller 工作节点和仲裁节点之间通过该端⼝同步 Everoute 的存储数据。 |
| Everoute Controller 仲裁节点 | Everoute Controller 工作节点 | 2379 | Everoute Controller 仲裁节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 仲裁节点和工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| CloudTower 虚拟机 | Everoute Controller 仲裁节点 | 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 仲裁节点中的 Everoute 组件。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |

## 网络负载均衡器

| 源端 | 目标端 | 目标端需开放的端口 | 端口说明 |
| --- | --- | --- | --- |
| CloudTower 虚拟机 | Everoute Controller 工作节点 | 6444 | 网络负载均衡器对外暴露 API， CloudTower 虚拟机通过该端口完成 API 调用。 |
| 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 中的组件。 |
| Everoute Controller 工作节点 | Everoute Controller 工作节点 | 2379 | 扩容时， Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| 8083 | Everoute Controller 工作节点通过该端口校验负载均衡请求的有效性。 |
| LB 虚拟机 | Everoute Controller 工作节点 | 6443 | LB 虚拟机通过该端口同步负载均衡相关资源。 |
| LB 虚拟机 | CloudTower 虚拟机 | 443 | LB 虚拟机通过该端口从获取关联的虚拟机网络信息。 |
| CloudTower 虚拟机 | LB 虚拟机 | 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级 LB 虚拟机中的组件。 |
| Everoute Controller 工作节点 | LB 虚拟机 | 9999 | Everoute Controller 工作节点通过该端口采集虚拟服务的 Metrics 数据。 |
| Everoute Controller 工作节点 | Everoute Controller 仲裁节点 | 30000 | Everoute Controller 工作节点通过该端口注册 etcd 成员信息。 |
| 30001 | Everoute Controller 工作节点和仲裁节点之间通过该端⼝同步 Everoute 的存储数据。 |
| Everoute Controller 仲裁节点 | Everoute Controller 工作节点 | 2379 | Everoute Controller 仲裁节点通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 仲裁节点和工作节点之间通过该端⼝同步 Everoute 的存储数据。 |
| CloudTower 虚拟机 | Everoute Controller 仲裁节点 | 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 仲裁节点中的 Everoute 组件。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |

## 网络安全导流

| 源端 | 目标端 | 目标端需开放的端口 | 端口说明 |
| --- | --- | --- | --- |
| CloudTower 虚拟机 | Everoute Controller 虚拟机 | 9443 | CloudTower 虚拟机通过该端口进行健康检查。 |
| 10000 | CloudTower 虚拟机通过该端口部署和升级 Everoute Controller 中的组件。 |
| Everoute Controller 虚拟机 | Everoute Controller 虚拟机 | 2379 | 扩容时， Everoute Controller 虚拟机通过该端口注册 etcd 成员信息。 |
| 2380 | Everoute Controller 虚拟机之间通过该端⼝同步 Everoute 的存储数据。 |
| 关联的集群中的主机 | Everoute Controller 虚拟机 | 6443 | 关联的集群中的主机通过该端口同步安全策略资源。 |
| CloudTower 虚拟机 | 关联的集群中的主机 | 8500 | 在将 SMTX OS（ELF）集群或 SMTX ELF 集群和 Everoute 进行关联时， CloudTower 虚拟机通过该端口注册 Everoute Controller 服务。 |
| 10000 | CloudTower 虚拟机通过该端口完成 Everoute agent 的部署和升级。 |
| 30002 | CloudTower 虚拟机通过该端口进行健康检查。 |
| Everoute Controller 虚拟机 | CloudTower 虚拟机 | 443 | Everoute agent 通过该端口从 CloudTower 同步虚拟机 深度包检测 配置。 |

---

## 部署前的准备 > 规划 Everoute Controller

# 规划 Everoute Controller

Everoute 服务的控制平面由一个或多个部署在 SMTX OS（ELF）集群或 SMTX ELF 集群的 Everoute Controller 组成，分布式防火墙功能、网络负载均衡器功能、虚拟专有云网络和网络安全导流功能的控制平面组件共享 Everoute Controller 的计算、存储资源。因此需根据使用的功能及 Everoute 服务所在集群的资源情况规划 Everoute Controller 的部署方式、工作节点和仲裁节点的数量、以及配置类型。

## 部署方式及数量

| 部署方式 | 数量 |
| --- | --- |
| 单集群部署 | 所有 Everoute Controller 工作节点部署在相同的集群。  可选组合如下：   - 如无需使用分布式防火墙功能或虚拟专有云网络功能，可选择部署 1 个、3 个或 5 个 Everoute Controller 工作节点。部署 1 个 Everoute Controller 时 Everoute 控制平面不具备高可用性，存在单点故障的风险，资源充足的情况下，建议部署 3 个或 5 个 Everoute Controller。 - 如需使用分布式防火墙功能或虚拟专有云网络功能，可选择部署 3 个或 5 个 Everoute Controller 工作节点。 |
| 跨集群部署 | Everoute Controller 工作节点、Everoute Controller 仲裁节点按需分布在 2-5 个不同的集群。  可选组合如下：   - 部署 3 个或 5 个 Everoute Controller 工作节点、无仲裁节点。 - 部署 2 个或 4 个 Everoute Controller 工作节点、1 个仲裁节点。 |
| 双活集群部署 | Everoute Controller 工作节点平均分布在双活集群的两个可用域、使用双活集群的仲裁节点作为 Everoute Controller 仲裁节点。  仅支持 6.0.0 及以上 6.x.x 版本的 SMTX OS (ELF) 双活集群。  可选组合如下：   - 部署 2 个 Everoute Controller 工作节点、1 个仲裁节点。 - 部署 4 个 Everoute Controller 工作节点、1 个仲裁节点。 |

## 配置类型

Everoute Controller 工作节点有如下三种不同的配置规格，可管理的功能数量不同，其占用的系统资源也不同。请根据下表规划 Everoute Controller 工作节点的配置。Everoute Controller 仲裁节点占用系统资源很低，无需单独规划。

| 配置类型 | 可管理的功能 | 占用的系统资源 |
| --- | --- | --- |
| **低配** | 最多可管理以下 2 个功能：  - 网络安全导流 - 分布式防火墙、网络负载均衡器、虚拟专有云网络中的任一功能 | - 2 vCPU - 2 GiB 内存 - 30 GiB 存储 |
| **中配** | 最多可管理以下 4 个功能：  - 网络安全导流 - 分布式防火墙 - 网络负载均衡器 - 虚拟专有云网络 | - 2 vCPU - 4 GiB 内存 - 30 GiB 存储 |
| **高配** | 最多可管理以下 4 个功能：  - 网络安全导流 - 分布式防火墙 - 网络负载均衡器 - 虚拟专有云网络 | - 4 vCPU - 8 GiB 内存 - 30 GiB 存储 |

如使用虚拟专有云网络功能，不同 Everoute Controller 配置类型可管理的虚拟专有云网络资源的数量上限建议如下表所示。

| 配置类型 | 主机数量 | VPC 数量 | VPC 子网数量 | 路由表数量 | 虚拟机网卡数量 | 安全策略数量 |
| --- | --- | --- | --- | --- | --- | --- |
| **低配** | 125 | 50 | 500 | 500 | 4000 | 400 |
| **中配** | 255 | 100 | 1000 | 1000 | 8000 | 800 |
| **高配** | 512 | 300 | 3000 | 3000 | 16000 | 1600 |

如使用网络负载均衡器功能，不同 Everoute Controller 配置类型可管理的虚拟服务资源的数量上限建议如下表所示。

| 配置类型 | 虚拟服务数量 |
| --- | --- |
| **低配** | 600 |
| **中配** | 1200 |
| **高配** | 2000 |

---

## 部署前的准备 > 规划虚拟专有云网络

# 规划虚拟专有云网络

如需启用虚拟专有云网络，网络架构图如下图所示：

![](https://cdn.smartx.com/internal-docs/assets/13269b6a/installation_guide_01.png)

- **管理网络**：用于集群管理。
- **存储网络**：用于集群内的主机之间的数据交换。
- **TEP IP 池**：用于向集群中的主机以及边缘网关虚拟机分配 TEP IP。当 LB 启用支持 VPC 后，还将用于向 LB 虚拟机分配 TEP IP。
- **内部服务子网**：用于向各个 VPC 的网关服务分配内部服务 IP。
- **外部子网**： 用于为边缘网关虚拟机指定数据平面与外部网络的接口，并划分地址段。

如需使用虚拟专有云网络功能，请根据如下要求和建议规划内部服务子网、TEP 网络和外部子网，规划前请您提前获取 SMTX OS（ELF）或 SMTX ELF 集群管理网络和存储网络的 IP 地址。

- **TEP IP 池**

  您可以根据 `TEP IP 数量 >（边缘网关虚拟机数量 + 关联的集群中的主机数量 + 需支持 VPC 网络的 LB 虚拟机数量 + 3）`规划 TEP IP 数量，请确保 IP 地址数量充足。

  允许添加多个 TEP IP 池，请您确保多个 TEP IP 池的地址间可以互通。

  TEP IP 池的地址建议不与集群管理网络和存储网络的 IP 地址重叠。
- **内部服务子网**

  默认使用 100.64.0.0/16，您也可以使用其他地址块，请确保 IP 地址数量充足以避免创建网关服务失败。

  请您确保内部服务子网和 VPC 子网的 CIDR 块不重叠；当 VPC 需要使用路由网关与外部网络通信时，请您确保内部服务子网、外部子网和 VPC 子网的 CIDR 块互不重叠。

  建议内部服务子网不与 TEP IP 池、集群管理网络和存储网络的 IP 地址重叠。
- **外部子网**

  建议外部子网不与 TEP IP 池、内部服务子网、集群管理网络和存储网络的 IP 地址重叠。

  建议规划 NAT 网关地址块和浮动 IP 地址块，L2 网关和路由网关可在使用时按需规划。

  当 VPC 需要使用路由网关与外部网络通信时，请您确保内部服务子网、外部子网和 VPC 子网的 CIDR 块互不重叠。

---

## 部署前的准备 > 规划 LB 虚拟机

# 规划 LB 虚拟机

网络负载均衡器的数据平面部署在一组或多组虚拟机内。一组虚拟机称为一个 LB 实例；两个 LB 实例可以组成 LB 实例组，以提供实例的高可用。

使用网络负载均衡器功能需提前规划 LB 实例或 LB 实例组的数量，以及单个 LB 实例中 LB 虚拟机数量和配置类型。

单个 LB 实例可选择的 LB 虚拟机数量及配置类型如下：

**数量**：2 个、3 个、4 个

**LB 虚拟机配置类型**

| **配置类型** | **LB 虚拟机管理能力** | **LB 虚拟机占用的系统资源** |
| --- | --- | --- |
| **低配** | - 30 个虚拟服务 - 100 个后端服务器 | - 2 vCPU - 4 GiB 内存 |
| **中配** | - 60 个虚拟服务 - 500 个后端服务器 | - 4 vCPU - 8 GiB 内存 |
| **高配** | - 150 个虚拟服务 - 1000 个后端服务器 | - 8 vCPU - 16 GiB 内存 |

**规划要求**

- 根据高可用要求，多个 LB 虚拟机需分布在 SMTX OS（ELF）集群或 SMTX ELF 集群的不同主机中，且 LB 虚拟机默认开启 CPU 独占，LB 虚拟机数量要求不多于集群中能够为其提供足够 vCPU 和内存的主机数量。
- 可根据 LB 虚拟机数量 \* 每个 LB 虚拟机可管理的虚拟服务和后端服务器数量，计算出单个 LB 实例总体可管理的范围。网络负载均衡器功能总体可管理的范围为所有 LB 实例可管理的范围之和，请根据实际业务要求搭配选择。
- 使用 LB 实例组时，其中主、备实例的**配置类型**、**虚拟机数量**均需要相同，且实例组中管理的资源数量不可超过单个 LB 实例（主或备）的可管理范围，以保证故障切换时顺利接管业务、保障业务的连续性。

---

## 安装部署 Everoute

# 规划 LB 虚拟机

网络负载均衡器的数据平面部署在一组或多组虚拟机内。一组虚拟机称为一个 LB 实例；两个 LB 实例可以组成 LB 实例组，以提供实例的高可用。

使用网络负载均衡器功能需提前规划 LB 实例或 LB 实例组的数量，以及单个 LB 实例中 LB 虚拟机数量和配置类型。

单个 LB 实例可选择的 LB 虚拟机数量及配置类型如下：

**数量**：2 个、3 个、4 个

**LB 虚拟机配置类型**

| **配置类型** | **LB 虚拟机管理能力** | **LB 虚拟机占用的系统资源** |
| --- | --- | --- |
| **低配** | - 30 个虚拟服务 - 100 个后端服务器 | - 2 vCPU - 4 GiB 内存 |
| **中配** | - 60 个虚拟服务 - 500 个后端服务器 | - 4 vCPU - 8 GiB 内存 |
| **高配** | - 150 个虚拟服务 - 1000 个后端服务器 | - 8 vCPU - 16 GiB 内存 |

**规划要求**

- 根据高可用要求，多个 LB 虚拟机需分布在 SMTX OS（ELF）集群或 SMTX ELF 集群的不同主机中，且 LB 虚拟机默认开启 CPU 独占，LB 虚拟机数量要求不多于集群中能够为其提供足够 vCPU 和内存的主机数量。
- 可根据 LB 虚拟机数量 \* 每个 LB 虚拟机可管理的虚拟服务和后端服务器数量，计算出单个 LB 实例总体可管理的范围。网络负载均衡器功能总体可管理的范围为所有 LB 实例可管理的范围之和，请根据实际业务要求搭配选择。
- 使用 LB 实例组时，其中主、备实例的**配置类型**、**虚拟机数量**均需要相同，且实例组中管理的资源数量不可超过单个 LB 实例（主或备）的可管理范围，以保证故障切换时顺利接管业务、保障业务的连续性。

---

## 安装部署 Everoute > 上传 Everoute 安装包

# 上传 Everoute 安装包

**准备工作**

获取 Everoute 安装包（`.tar.gz` 文件）。

**注意事项**

您需要根据规划中 Everoute Controller 所属集群、LB 实例所属集群、边缘网关所属集群、分布式防火墙及虚拟专有云网络需关联集群的 CPU 架构上传相应架构的安装包。

**操作步骤**

1. 登录 CloudTower，进入**网络与安全**界面，在左侧导航栏中单击**设置**。
2. 在弹出的窗口中，单击**安装包管理**，再单击右上角的 **+ 上传安装包**，上传 `.tar.gz` 格式的安装包。
3. 单击**上传**。

---

## 安装部署 Everoute > 部署 Everoute 服务

# 部署 Everoute 服务

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**。
2. 在弹出的页面左侧位置单击 **+ 部署 Everoute 服务**，进入配置信息页面。
3. 根据页面提示按需完成[基本信息](/everoute/3.5.0/er_installation_guide/installation_guide_13)、[Everoute Controller](/everoute/3.5.0/er_installation_guide/installation_guide_14)、[分布式防火墙](/everoute/3.5.0/er_installation_guide/installation_guide_15)、[虚拟专有云网络](/everoute/3.5.0/er_installation_guide/installation_guide_35)和[网络负载均衡器](/everoute/3.5.0/er_installation_guide/installation_guide_16)配置。
4. 完成配置后，单击**部署**，系统将自动在集群上完成 Everoute 服务的部署。

   > **注意**：
   >
   > Everoute 服务使用 CloudTower 的 NTP 服务器进行时间同步，部署完成后请参考《CloudTower 使用指南》的**配置 NTP 服务器**章节，确保 CloudTower 中已正确配置了 NTP 服务器，以免影响 Everoute 服务的正常运行。

---

## 安装部署 Everoute > 部署 Everoute 服务 > 配置基本信息

# 配置基本信息

1. 为待部署的 Everoute 服务设置名称，并按需选择要部署的版本。
2. 选择如下至少一项在 Everoute 服务中需启用的功能。

   - 分布式防火墙
   - 虚拟专有云网络
   - 网络负载均衡器
   - 网络安全导流

   如需为虚拟专有云网络内的客户端或后端服务器提供负载均衡功能，请同时启用虚拟专有云网络和网络负载均衡器功能。

---

## 安装部署 Everoute > 部署 Everoute 服务 > 配置 Everoute Controller

# 配置 Everoute Controller

**前提条件**

已完成 [Everoute Controller 的相关规划](/everoute/3.5.0/er_installation_guide/installation_guide_07)。

**注意事项**

- 跨集群或双活集群部署时，建议确保任一集群或可用域中分布的 Everoute Controller 数量不超过总体 Everoute Controller 数量的一半，以保证当任一集群或可用域发生故障时，仍有一半以上节点存活，从而保证 Everoute 服务正常运行。

  - Everoute Controller 总数为 3 时，单个集群或可用域中建议部署 1 个节点。
  - Everoute Controller 总数为 5 时，单个集群或可用域中建议部署 1 ～ 2 个节点。
- 若 Everoute Controller 所属集群发生以下变化，则可以支持将 Everoute Controller 平均分布在优先、次级可用域，并支持复用双活集群仲裁节点。

  - 从 5.0.1 及以上 5.x.x 版本双活集群升级至 6.0.0 及以上 6.x.x 版本双活集群。
  - 从 6.0.0 及以上 6.x.x 版本未启用双活特性的集群转换为双活集群。

  为确保分布均匀、提供高可用，请在集群变化后对 Everoute Controller 节点进行逐个[替换](/everoute/3.5.0/er_installation_guide/installation_guide_31#%E6%9B%BF%E6%8D%A2-everoute-controller-%E8%8A%82%E7%82%B9)。

  - 如原先为 3 个 Everoute Controller 节点，需将 1 个节点替换至次级可用域，1 个节点替换为仲裁节点。
  - 如原先为 5 个 Everoute Controller 节点，需将 2 个节点替换至次级可用域，1 个节点替换为仲裁节点。
- 若 CloudTower 已启用高可用功能，则可以支持复用 CloudTower 高可用仲裁节点。启用 CloudTower 高可用功能的具体操作，请参考《CloudTower 安装与运维指南》的**部署高可用集群**章节。

**操作步骤**

1. 选择 Everoute Controller 的配置类型。
2. 设置 Everoute Controller 工作节点。

   - **所属集群**：选择部署 Everoute Controller 工作节点的集群。单击**查看管理网络信息**，可辅助填写相关参数。
   - **子网掩码**：输入 Everoute Controller 工作节点管理 IP 地址的子网掩码。
   - **网关**：输入 Everoute Controller 工作节点的网关地址。
   - **工作节点**：

     - **虚拟机网络**：选择 Everoute Controller 工作节点使用的虚拟机网络，需为 Access 类型的 VLAN 网络。
     - **IP 地址**：根据网络管理员提供的 IP 地址分配表，设置 Everoute Controller 工作节点的管理 IP 地址。
   > **说明**：
   >
   > 当 Everoute Controller 工作节点的所属集群选择双活集群时，根据双活集群版本不同，配置参数稍有差异。
   >
   > - 对于 6.0.0 及以上 6.x.x 版本的 SMTX OS (ELF) 双活集群，需设置**节点数量**，支持选择 2 个或 4 个。之后需按照**优先可用域**、**次级可用域**分别设置子网掩码、网关、以及工作节点的虚拟机网络和管理 IP 地址。
   > - 对于 5.0.1 及以上 5.x.x 版本的 SMTX OS (ELF) 双活集群，将被视为普通集群使用，因此与普通集群配置参数完全一致，所有工作节点均位于双活集群的优先可用域中。
3. （可选）单击 **+ 添加工作节点**，按照[规划的 Everoute Controller 数量](/everoute/3.5.0/er_installation_guide/installation_guide_07#%E9%83%A8%E7%BD%B2%E6%96%B9%E5%BC%8F%E5%8F%8A%E6%95%B0%E9%87%8F)继续设置其他工作节点的参数。单击 **x**，可移除工作节点。

   当存在多个工作节点时，可根据网络管理员提供的 IP 地址分配表在 **IP 地址**中输入起始 IP，系统将根据此 IP 地址为所有 Everoute Controller 工作节点自动分配连续的管理 IP 地址。
4. （可选）当 Everoute Controller 工作节点需要部署在多个集群时，您可以单击 **+ 添加所属集群**，继续设置其他集群中的工作节点参数。
5. 对于跨集群部署方式，您可以按需启用**仲裁节点**并选择一个已有的仲裁节点；对于双活集群部署方式，仲裁节点默认启用，需选择一个已有的仲裁节点。支持复用双活集群仲裁节点或 CloudTower 高可用仲裁节点。

---

## 安装部署 Everoute > 部署 Everoute 服务 > 配置分布式防火墙

# 配置分布式防火墙

1. 选择是否启用**默认拒绝通信**。

   Everoute 服务中的虚拟机未应用自定义安全策略或隔离策略时，若启用该项，则不允许该虚拟机接收或发出任意流量；若不启用该项，则允许该虚拟机接收或发出任意流量。

   > **注意**：
   >
   > - 该设置仅可对此类虚拟机生效：任一虚拟机网络所属的虚拟分布式交换机已关联该 Everoute 服务，并且未作为策略对象。
   >
   >   如果虚拟机包含多个虚拟网卡，其中仅部分网卡所属的虚拟分布式交换机已关联该 Everoute 服务，则该设置仅对这部分网卡中的流量生效。
   > - 该设置将在 Everoute 部署成功后生效。
2. 创建**全局白名单**并选择是否立即启用。

   在已启用默认拒绝通信或已设置自定义安全策略的情况下，全局白名单可以确保用户在数据中心之外部署的服务（例如堡垒机）与数据中心内的虚拟机正常通信。

   - 选择是否立即启用全局白名单。

     > **说明**：
     >
     > 搭配使用可观测性 1.2.0 及以上版本的网络流量可视化功能时，您可以在部署 Everoute 阶段配置全局白名单，但暂不启用。在部署完成后，正常运行一段时间相关业务后，打开网络流量可视化的**预览预期效果**开关，来观察当前的数据流和全局白名单生效后的预期数据流。若发现数据流的预期类型和期望不符，您可以参考《Everoute 分布式防火墙管理指南》的[编辑全局安全策略](/everoute/3.5.0/er_administration_guide_dfw/administration_guide_dfw_14#%E7%BC%96%E8%BE%91%E5%85%A8%E5%B1%80%E5%AE%89%E5%85%A8%E7%AD%96%E7%95%A5)再次编辑全局白名单，继续运行一段时间业务后再次观察数据流的预期类型，直到满足期望再开启全局白名单。通过这种方式，您可以在全局白名单实际生效前直观了解其影响，提前发现和解决潜在的安全问题，且不会对正常运行的业务流量产生任何实际影响。具体操作请参考《Everoute 分布式防火墙管理指南》的[安全策略监控模式](/everoute/3.5.0/er_administration_guide_dfw/administration_guide_dfw_112)。
   - 单击 **+ 添加 IP 地址**，可以为虚拟机配置出入流量白名单。若不启用全局白名单，则该操作为可选。

     1. **添加入/出流量 IP 地址白名单**：支持 IPv4、IPv6，可输入 IP 地址、CIDR 块或 IP 地址范围。输入 CIDR 块后，还可以单击输入框右侧 **...**，单击**排除部分 IP 地址**，手动从已输入的 CIDR 块中排除特定 IP 地址或 CIDR 块。
     2. **协议**：可选择**指定**后输入允许通过的协议及端口，或选择特定服务。如无需限制协议可选择**任意**。
   > **注意**：
   >
   > - 全局白名单仅可对此类虚拟机生效：任一虚拟机网络所属的虚拟分布式交换机已关联该 Everoute 服务，并且未被隔离。
   >
   >   如果虚拟机包含多个虚拟网卡，其中仅部分网卡所属的虚拟分布式交换机已关联该 Everoute 服务，则全局白名单仅对这部分网卡中的流量生效。
   > - 全局白名单中填写的 IP 地址需为 Everoute 服务范围外的 IP 地址，如白名单中包含已被 Everoute 关联的集群中的虚拟机，则全局白名单不会对此类虚拟机设置对称的流量规则，因此无法保证此虚拟机可以访问 Everoute 服务已关联的其他虚拟机，具体的流量处理方式将取决于此类虚拟机所属的其他安全策略。

---

## 安装部署 Everoute > 部署 Everoute 服务 > 配置虚拟专有云网络

# 配置虚拟专有云网络

1. 填写内部服务子网的 **CIDR 块**。
2. 填写至少一个 TEP IP 池信息，包括**名称**、**起始 IP**、**结束 IP**、**子网掩码**和**网关**。

---

## 安装部署 Everoute > 部署 Everoute 服务 > 配置网络负载均衡器

# 配置网络负载均衡器

部署阶段仅支持创建一个 LB 实例，即一组用于部署 LB 服务的虚拟机。如需创建更多 LB 实例或创建 LB 实例组，可在部署完成后进入 **LB 实例**或 **LB 实例组**页面进行配置。

**操作步骤**

1. 填写 LB 实例的**名称**和**描述**信息，选择部署 LB 实例的集群。
2. 选择部署的**负载均衡虚拟机数量**。
3. 根据您计划管理的虚拟服务和后端服务器数量，选择 LB 虚拟机的**配置类型**。
4. 当 Everoute 服务中已配置虚拟专有云网络功能时，可选择是否**支持 VPC**。启用后，可为 VPC 网络内的客户端或后端服务器提供负载均衡功能。
5. 批量设置 LB 虚拟机的管理 IP 地址、子网掩码和网关。单击**查看管理网络信息**，可辅助填写相关参数。

   - **起始 IP 地址**：（可选）根据网络管理员提供的 IP 地址分配表，在此输入 LB 虚拟机的起始管理 IP 后，系统将根据此 IP 地址为所有 LB 虚拟机自动分配连续的管理 IP 地址。
   - **子网掩码**：输入 LB 虚拟机管理 IP 地址的子网掩码。
   - **网关**：输入 LB 虚拟机管理网络的网关地址。
6. 分别为每个 LB 虚拟机设置管理网络。若您已启用**支持 VPC**，还需为每个 LB 虚拟机设置 TEP 网络。

   - **管理网络**：

     - **虚拟机网络**：选择 LB 虚拟机管理网络使用的虚拟机网络。该网络需为 Access 类型的 VLAN 网络，并且能够与 Everoute Controller 连通。
     - **IP 地址**：若上一步中已设置 LB 虚拟机的起始管理 IP 地址，此处显示的 IP 地址为系统自动分配的管理 IP 地址。您也可以根据网络管理员提供的 IP 地址分配表，手动输入为 LB 虚拟机分配的管理 IP 地址。
   - **TEP 网络**：

     - **虚拟机网络**：选择 LB 虚拟机用于 TEP 网络通信的虚拟机网络。该网络需为 Access 类型的 VLAN 网络，并且能够与 VPC 已关联集群中的 TEP 网络连通。如 LB 的 VIP 或 LIP 地址需要通过 VPC 网关与外部通信，此网络也需要与 VPC 边缘网关的 TEP 网络连通。
     - **TEP 地址**：选择虚拟专有云网络中已创建的 TEP IP 池，并设置属于该 IP 池的 TEP IP 地址，留空则将从 TEP IP 池中自动分配。

---

## （可选）关联可观测性服务

# （可选）关联可观测性服务

建议在可观测性平台中将 Everoute 服务关联至一个可观测性服务中，以使用可观测性服务提供的网络流量可视化、监控报警等功能，详情请参考对应版本《可观测性平台用户指南》的**关联系统服务**章节。

---

## 管理 Everoute Controller

# 管理 Everoute Controller

Everoute 部署完成之后，您可以增加 Everoute Controller 数量、提高资源配置、编辑 Everoute Controller 工作节点、替换 Everoute Controller 工作节点或仲裁节点。

## 查看 Everoute Controller 信息

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller** 即可查看如下信息：

   - Everoute Controller 总数，以及工作节点和仲裁节点的数量。
   - 配置类型。
   - 按所属集群分区域展示各 Everoute Controller 工作节点的信息，以及 vCPU、内存和存储容量的总量和使用率。
   - Everoute Controller 仲裁节点信息。

> **说明**：
>
> 如果 vCPU、内存、存储的总量和使用率数据无法显示，有以下两个可能的原因：
>
> - Everoute Controller 工作节点所属集群未部署高级监控且未关联 1.2.0 或以上版本的可观测性服务。
>
>   当集群已采集的监控数据量即将达到基本监控的预留资源上限时，虚拟机的一些指标将停止采集。请您参考《CloudTower 使用指南》的**管理高级监控**章节部署高级监控，或参考《可观测性平台用户指南》的**部署可观测性服务**章节部署可观测性服务。
> - Everoute Controller 工作节点虚拟机异常。
>
>   虚拟机状态处于`更新中`、`暂停`、`关机`或`未知`时无法获取相关指标，请先将虚拟机恢复正常。

## 增加 Everoute Controller 数量

您可以按需增加 Everoute Controller 的数量，以提高 Everoute 服务的可用性。

启用分布式防火墙或虚拟专有云网络功能前，需将 Everoute Controller 节点数量增加至 `3 个`或 `5 个`。

**注意事项**

新增 Everoute Controller 节点的管理 IP 地址需与其他 Everoute Controller 节点之间的管理 IP 地址相互连通。

**操作步骤**

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller**，进入配置页面。
3. 在 **Everoute Controller 数量**右侧单击**增加**。
4. 参考[配置 Everoute Controller](/everoute/3.5.0/er_installation_guide/installation_guide_14)，为此次增加的 Everoute Controller 节点配置虚拟机网络及管理 IP 地址。
5. 单击**保存**。

## 提高 Everoute Controller 配置

如需同时启用两个及两个以上的功能，需提升 Everoute Controller 配置类型，使其至少为`中配`。

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller**，进入配置页面。
3. 在**配置类型**右侧单击**提高**。
4. 选择配置类型，单击**保存**。

## 编辑 Everoute Controller 工作节点

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller**，进入配置页面。
3. 单击 Everoute Controller 工作节点某一所属集群区域右上角的**编辑**，可同时编辑该集群中所有工作节点的子网掩码、网关、以及节点虚拟机网络和管理 IP 地址，编辑相关信息将导致 Everoute 系统服务的管理网络短暂中断。具体参数说明，请参考[配置 Everoute Controller](/everoute/3.5.0/er_installation_guide/installation_guide_14)。

   > **说明**：
   >
   > 编辑 Everoute Controller 管理 IP 时，建议将 Everoute Controller 管理 IP 所在网段与 LB VIP 所在网段严格分开，以避免可能存在的路由覆盖导致的网络异常。
4. 单击**保存**。

## 替换 Everoute Controller 节点

替换 Everoute Controller 节点，相当于删除当前节点，并创建一个新的节点。

- 当某个 Everoute Controller 节点故障且无法恢复时，可在当前集群内以相同的配置信息进行替换，系统将删除原故障节点，并重新创建一个相同配置的 Everoute Controller 节点。
- 当需要将 Everoute Controller 跨集群迁移至新集群时，可逐个对需要迁移的节点进行替换，替换时填写迁移的目标集群信息，以及 Everoute Controller 在新集群中的管理 IP 地址。

**注意事项**

- 替换的 Everoute Controller 节点的管理 IP 地址需与其他 Everoute Controller 节点之间的管理 IP 地址相互连通。
- 为保证节点替换期间 Everoute 服务正常运行，请确保除待替换节点外，仍存在半数以上的 Everoute Controller 节点处于正常状态。

**操作步骤**

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller**，进入配置页面。
3. 单击某一节点右侧的 **...** > **替换节点**。

   - **替换工作节点**：

     - 若当前已存在 Everoute Controller 仲裁节点，新节点默认为**工作节点**，需指定新节点的所属集群、IP 地址、子网掩码、虚拟机网络等信息。
     - 若当前不存在 Everoute Controller 仲裁节点，可按需选择新节点为**工作节点**或**仲裁节点**，并完成相应配置。
   - **替换仲裁节点**：

     可选择其他已有的仲裁节点，也可以按需将**仲裁节点**切换为**工作节点**并完成相应配置。
4. 单击**替换**。

## 恢复 Everoute Controller 状态

当 Everoute Controller 同步状态异常时，页面上方会出现异常提示，此时您可以重新同步并恢复 Everoute Controller 的状态。

**操作步骤**

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**，选择 Everoute 服务。
2. 在**服务运维**中单击 **Everoute Controller**，进入配置页面。
3. 在**同步状态异常**提示信息右侧单击**恢复**。

---

## 升级 Everoute 服务

# 升级 Everoute 服务

Everoute 服务支持一键在线热升级。在升级过程中，Everoute 服务可以正常运行，但不支持变更已有配置。

**准备工作**

参考《Everoute 发布说明》的[版本配套说明](/everoute/3.5.0/er_release_notes/release_notes_02)，确认目前使用的 SMTX OS（ELF）集群或 SMTX ELF 集群版本和 CloudTower 版本满足要求。

**注意事项**

- 当 CloudTower 升级至 4.1.0 及以上版本后，如您原先同时具有分布式防火墙和网络负载均衡器的正式许可（**订阅许可**或**永久许可**），则升级后将仅具有分布式防火墙的正式许可，网络负载均衡器会变更为**试用许可**。请联系 SmartX 客户经理，重新申请并更新网络负载均衡器的许可。
- 当 Everoute 从 3.3.0 之前的版本升级至本版本后，由于防火墙安全策略新增对 IPv6 的支持，非白名单内的 IPv6 地址将默认被拒绝，请在升级完成后手动配置所需的 IPv6 白名单。
- 若 Everoute 服务部署在 6.0.0 及以上 6.x.x 版本的 SMTX OS（ELF）双活集群中，当 Everoute 从 3.4.0 之前的版本升级至本版本后，支持将 Everoute Controller 平均分布在优先、次级可用域，并支持复用双活集群仲裁节点。

  为确保分布均匀、提供高可用，请在升级完成后对 Everoute Controller 节点进行逐个[替换](/everoute/3.5.0/er_installation_guide/installation_guide_31#%E6%9B%BF%E6%8D%A2-everoute-controller-%E8%8A%82%E7%82%B9)。

  - 如升级前为 3 个 Everoute Controller 节点，需将 1 个节点替换至次级可用域，1 个节点替换为仲裁节点。
  - 如升级前为 5 个 Everoute Controller 节点，需将 2 个节点替换至次级可用域，1 个节点替换为仲裁节点。
- 若 CloudTower 已启用高可用功能，当 Everoute 从 3.5.0 之前的版本升级至本版本后，支持复用 CloudTower 高可用仲裁节点。启用 CloudTower 高可用功能的具体操作，请参考《CloudTower 安装与运维指南》的**部署高可用集群**章节。

**操作步骤**

1. 进入 CloudTower 的**网络与安全**界面，在左侧导航栏中单击**设置**。
2. 在弹出的窗口中单击**安装包管理**，如安装包列表中已有目标版本的安装包，请直接从第 4 步开始操作。
3. 单击右上角的 **+ 上传安装包**，上传目标版本的 `.tar.gz` 格式的安装包。
4. 选择待升级的 Everoute 服务。
5. 在**服务运维**中单击**服务升级**，进入服务升级界面，选择目标版本开始升级。

---

## 卸载 Everoute 服务

# 卸载 Everoute 服务

当不再需要某个 Everoute 服务，想要将其卸载时，请确认该 Everoute 服务同时满足以下条件：

- 没有关联集群
- 不存在 LB 实例及 LB 实例组
- 不存在边缘网关及边缘网关组

**风险提示**

卸载 Everoute 服务后，将无法使用该 Everoute 服务及该 Everoute 服务已开启的功能，且无法恢复，请谨慎操作。

**操作步骤**

1. 登录 CloudTower，进入**网络与安全**界面，选择**设置**，选择要卸载的 Everoute 服务。
2. 在**服务运维**中单击**卸载**。
3. 在弹出的**卸载**对话框中单击**卸载**。

---

## 版权信息

# 版权信息

版权所有 © 2026 北京志凌海纳科技股份有限公司（SmartX）保留一切权利。

本文档和本文档包含的全部信息受中华人民共和国法律法规及国际公约对知识产权的管辖和保护。本文档和本文档包含的全部信息的版权由 SmartX 或其许可方所有。未经 SmartX 书面许可，不得以任何方式，包括但不限于电子、机械或光学的方式对本文档内容的部分或全部进行复制、修改、传播、经销、翻印、拆解、存储在检索系统中或其他任何形式的使用。本文档中出现的所有非 SmartX 的公司名称、产品名称和服务名称仅用于识别目的，可能是其各自所有者的注册商标、商标或服务标记，不应被视为未经其所有者书面许可而授予使用前述任何商标、标志的许可或权利，亦不代表该所有者对任何产品或服务信息的授权使用或背书。
