# Everoute 支持仲裁节点

## 

| 修订时间 | 修订者 | 描述 |
| :---- | :---- | :---- |
| 2025-01-06 | [Wang Zhan](mailto:wang.zhan@smartx.com) | draft |
| 2025-02-28 | [Wang Zhan](mailto:wang.zhan@smartx.com) | 仲裁节点说明 |

# **背景介绍**

Everoute 希望提供跨集群的容灾能力，当有足够可用集群时，可以使用 1 \+ 1 \+ 1 或者 1 \+ 2 \+ 2 的部署模式。

同时引入仲裁节点的概念。在 Everoute 中，仲裁节点并非用来裁定哪个控制器虚拟机处于 active 状态，而是作为 etcd node 存在，提供 leader 选举能力。仲裁节点可以理解为简化的控制器节点，相比于普通控制器节点，仲裁节点拥有更加灵活的部署方式、更少的资源占用。

# **仲裁节点**

仲裁节点只包含 etcd 服务和少量的管理组件（监控、指标采集等）。对于外部仲裁节点，Everoute 只负责管理仲裁节点上 everoute 相关的服务，不负责管理仲裁节点本身的生命周期。仲裁节点可以是物理主机或虚拟机，只需要满足**特定条件**即可作为 everoute 服务的仲裁节点：

| 资源 | 要求 | 备注 |
| :---- | :---- | :---- |
| 计算 | 2C 2G（待定，可能更低。1C 1G？） | 谁来管理资源？简单的方式可以通过容器 cgroup 来管理。仲裁节点也可以提供特定的 cgroup parent |
| 网络 | 包含可与 everoute 控制器虚拟机联通的管理网络 IP 可独占的几个管理网端口（用于 etcd 通信和健康检查） 到 everoute 控制器虚拟机延迟和带宽要求 | everoute 运维管理需要提供一种变更仲裁节点 IP 的接口 如何/是否自动感知仲裁节点 IP 变更？ |
| 防火墙 | 需要开放 everoute 需要的管理网端口 |  |
| 存储 | 10 GiB 存储空间。用于存储 etcd 等数据和日志 |  |
| 容器运行时 | 需要 containerd 作为容器运行时 需要通过 tcp 暴露 containerd 接口 | 关于 2：例如安装了 containerd-proxy-service rpm（目前 vm 上的方式）或者通过 envoy 配置了 containerd 的代理端口（目前 host 上的方式） |

理论上多个 everoute 可以复用同一个仲裁节点，~~是否需要在产品产品层面实现待定~~（需要）。

## **外部仲裁节点**

其它产品里有一些已存在的仲裁节点，可以考虑作为 everoute 外部仲裁节点使用。

### **双活集群仲裁节点**

600 后[支持 containerd 和管理网络 IP](https://docs.google.com/document/d/18EDfHHJldqd0sEbIVfoeE8Ftjrg_ExR9B8uYQb67VGc/edit?tab=t.0)，基本满足 everoute 仲裁节点的要求。

同时仲裁节点相对较为独立，可以很好的承担跨集群容灾过程中的仲裁角色。

### **CloudTower 仲裁节点**

CloudTower 仲裁节点承载着自动判定 && 切换主备 tower 的功能。活动节点、备份节点、仲裁节点为部署在同一个集群、两个集群或者三个集群上的三个虚拟机。

当前 tower 仲裁节点仅要求包含 HA 网络，可以没有管理网络。如果支持 everoute 部署，需要支持配置管理网络 IP。

~~如果当前 tower 下存在少于三集群，则使用 tower 仲裁节点意义不大。如果 tower 下多于三集群，则可以使用 1 \+ 1 \+ 1 模式作为 1 \+ 1 \+ 仲裁的替代方案。另外加上使用 tower 仲裁节点需要额外的改造成本，收益不大，不建议考虑使用 tower 仲裁节点这种方式。~~

对于两个集群，如果 tower 仲裁节点部署到外部环境中，则 everoute 可以使用 tower 仲裁节点，通过 1 \+ 1 \+ 仲裁的方式来实现跨集群的高可用能力。

## **调研**

[https://docs.harvesterhci.io/v1.3/advanced/witness/](https://docs.harvesterhci.io/v1.3/advanced/witness/)

表格

|  |  |  |  |
| :---- | :---- | :---- | :---- |
|  |  |  |  |
