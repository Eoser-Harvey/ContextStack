# 交换机PBR（策略路由）功能分析

## 话题信息
- **话题名称**：交换机PBR功能分析
- **创建时间**：2026-05-11
- **最后更新**：2026-05-11
- **当前状态**：活跃

## 自动上下文加载
- **全局规则**：D:\MyFile\AI\ContextStack\GLOBAL-RULES.md
- **相关文档**：
  - 02-Knowledge/system/research-frameworks/tech-research-framework.md（当需要技术调研时）
  - 02-Knowledge/skills/network-packet-analysis/network-packet-analysis-guide.md（当需要网络分析时）
- **记忆索引**：D:\MyFile\AI\ContextStack\MEMORY.md

## 话题目标
深入理解交换机PBR（Policy-Based Routing）策略路由功能，包括其工作原理、应用场景，以及在IPv4、IPv6及双栈环境下的具体实现和配置差异。

## 相关知识

### 1. PBR概述
**PBR（Policy-Based Routing）** 是一种基于策略的路由选择机制，允许网络管理员根据预定义的条件（如源地址、协议类型、端口号等）来决定数据包的转发路径，而不是仅仅依赖目的IP地址进行传统路由决策。

**核心价值**：
- **流量工程**：优化网络路径，提高带宽利用率
- **负载均衡**：将流量分散到多条链路上
- **服务质量(QoS)**：为特定流量提供优先级或保证带宽
- **安全策略**：实现基于策略的访问控制和流量隔离

### 2. PBR工作原理
PBR通过以下关键组件实现：
- **匹配条件（Match Criteria）**：定义流量分类规则
  - 源IP地址/子网
  - 目的IP地址/子网
  - 协议类型（TCP/UDP/ICMP等）
  - 端口号（源端口/目的端口）
  - DSCP/TOS字段
- **操作动作（Set Actions）**：定义匹配后的转发行为
  - 设置下一跳地址
  - 设置出接口
  - 设置优先级/服务类型
  - 标记/重标记流量
- **策略映射（Route-Map）**：将匹配条件和操作动作关联起来

### 3. 配置要素
```
1. 定义访问控制列表（ACL）识别流量
2. 创建路由映射（Route-Map）定义策略
3. 在接口上应用路由映射
```

### 4. 主要应用场景
| 场景 | 描述 | 典型配置 |
|------|------|----------|
| **负载均衡** | 将不同来源的流量分配到不同出口 | 基于源IP的PBR |
| **链路备份** | 主链路故障时自动切换到备用链路 | 基于优先级的路由映射 |
| **服务质量** | 为关键业务流量提供高优先级路径 | 基于DSCP的PBR |
| **流量分离** | 将特定流量引导到专用设备（如防火墙） | 基于协议/端口的PBR |
| **多ISP接入** | 根据流量类型选择不同的ISP出口 | 基于目的端口的PBR |

## 5. IPv4与IPv6 PBR对比

### IPv4 PBR特点
- **配置命令**：基于传统IPv4 ACL和路由映射
- **匹配条件**：
  - `access-list` 标准/扩展ACL
  - `ip address` 源/目的地址
  - `protocol` 协议类型
  - `port` 端口号
- **设置动作**：
  - `set ip next-hop` 设置IPv4下一跳
  - `set interface` 设置出接口
  - `set ip precedence` 设置优先级
  - `set ip dscp` 设置DSCP值

### IPv6 PBR特点
- **配置命令**：使用IPv6 ACL和路由映射
- **匹配条件**：
  - `ipv6 access-list` IPv6 ACL
  - `source-address` IPv6源地址
  - `destination-address` IPv6目的地址
  - `protocol` 协议类型（同IPv4）
  - `port` 端口号（同IPv4）
- **设置动作**：
  - `set ipv6 next-hop` 设置IPv6下一跳
  - `set interface` 设置出接口（同IPv4）
  - `set traffic-class` 设置流量类别（类似IPv4的TOS）
  - `set ipv6 dscp` 设置IPv6 DSCP值

### 关键差异
| 对比项 | IPv4 PBR | IPv6 PBR |
|--------|----------|----------|
| **ACL类型** | 标准/扩展IPv4 ACL | IPv6 ACL |
| **地址格式** | 32位点分十进制 | 128位十六进制 |
| **下一跳设置** | `set ip next-hop` | `set ipv6 next-hop` |
| **优先级字段** | IP Precedence/TOS | Traffic Class/Flow Label |
| **配置复杂度** | 相对简单，成熟 | 较新，需注意地址长度 |

## 6. 双栈环境下的PBR策略

### 双栈PBR配置原则
1. **独立配置**：IPv4和IPv6 PBR需要分别配置
2. **策略协调**：确保两种协议的策略逻辑一致
3. **资源管理**：注意ACL和路由映射的资源占用

### 典型双栈PBR场景
- **协议感知路由**：根据IP协议版本选择不同路径
- **负载均衡增强**：同时利用IPv4和IPv6链路进行负载分担
- **故障切换**：当一种协议路径故障时，通过另一种协议提供备份

### Comware V7与V9差异说明

H3C Comware V7和V9在PBR策略路由的核心配置命令上基本一致，主要命令结构相同（`policy-based-route`、`if-match`、`apply`、`ip policy-based-route`等），两者无显著差异。以下配置示例同时适用于V7和V9。

> **注意**：V9在部分高级特性上有所增强（如SRv6策略路由、更丰富的匹配条件等），但基础PBR配置命令与V7一致。

### 配置示例（H3C Comware V7/V9 通用）
```bash
# ============================================================
# IPv4 PBR配置
# ============================================================

# 1. 定义ACL匹配流量
acl advanced 3000
 rule 0 permit ip source 192.168.1.0 0.0.0.255
#
# 2. 创建策略路由
policy-based-route PBR-EXAMPLE permit node 10
 if-match acl 3000
 apply next-hop 10.1.1.1
#
# 3. 在接口上应用策略路由
interface GigabitEthernet1/0/1
 ip address 192.168.1.1 255.255.255.0
 ip policy-based-route PBR-EXAMPLE

# ============================================================
# IPv6 PBR配置
# ============================================================

# 1. 定义IPv6 ACL匹配流量
acl ipv6 advanced 3000
 rule 0 permit ipv6 source 2001:db8::/32
#
# 2. 创建IPv6策略路由
ipv6 policy-based-route PBR-IPv6-EXAMPLE permit node 10
 if-match acl ipv6 3000
 apply next-hop 2001:db8::1
#
# 3. 在接口上应用IPv6策略路由
interface GigabitEthernet1/0/1
 ipv6 address 2001:db8::1/64
 ipv6 policy-based-route PBR-IPv6-EXAMPLE

# ============================================================
# 查看策略路由状态
# ============================================================
display ip policy-based-route
display ipv6 policy-based-route
display ip policy-based-route interface GigabitEthernet1/0/1

# ============================================================
# PBR高级配置（匹配条件扩展）
# ============================================================

# 基于源IP + 目的IP + 协议 + 端口的多条件匹配
acl advanced 3001
 rule 0 permit tcp source 192.168.1.0 0.0.0.255 destination 10.0.0.0 0.255.255.255 destination-port eq 80
#
policy-based-route PBR-WEB permit node 10
 if-match acl 3001
 apply next-hop 10.1.1.100

# 设置多个下一跳（负载分担/备份）
policy-based-route PBR-REDUNDANT permit node 10
 if-match acl 3000
 apply next-hop 10.1.1.1
 apply next-hop 10.1.2.1

# 设置默认下一跳（仅当路由表中无精确匹配路由时生效）
policy-based-route PBR-DEFAULT permit node 10
 if-match acl 3000
 apply default-next-hop 10.1.1.1

# 设置出接口（适用于点对点链路）
policy-based-route PBR-INTERFACE permit node 10
 if-match acl 3000
 apply output-interface GigabitEthernet1/0/2

# ============================================================
# Comware V9 增强特性（V7不支持）
# ============================================================

# V9支持SRv6策略路由（将匹配流量引导至SRv6隧道）
# ipv6 policy-based-route PBR-SRv6 permit node 10
#  if-match acl ipv6 3000
#  apply srv6-policy endpoint 2001:db8::1
```

## 7. 实践建议与注意事项

### 最佳实践
1. **明确策略目标**：在配置前清晰定义流量工程目标
2. **逐步实施**：先在非关键链路测试，再逐步推广
3. **监控验证**：配置后使用`display ip policy-based-route`等命令验证策略生效
4. **文档记录**：详细记录策略逻辑和配置变更

### 常见问题
- **策略冲突**：多个PBR策略可能产生冲突，需注意优先级
- **性能影响**：复杂的匹配条件可能影响转发性能
- **维护复杂度**：策略越多，网络维护越复杂
- **故障排查**：PBR可能隐藏传统路由问题，增加故障排查难度

### 双栈环境特殊考虑
- **协议优先级**：明确IPv4和IPv6流量的优先级关系
- **地址规划**：合理的IPv4/IPv6地址规划有助于简化PBR配置
- **迁移策略**：在IPv4向IPv6迁移过程中，PBR策略需要平滑过渡

## 相关资源
- **厂商文档**：
  - H3C交换机策略路由配置指南
  - H3C Comware V7网络设备配置手册
- **标准参考**：
  - RFC 791 (IPv4)
  - RFC 2460 (IPv6)
  - RFC 4291 (IPv6寻址架构)
- **工具脚本**：
  - 策略路由验证脚本
  - 双栈PBR配置模板

## 会话历史
| 日期 | 讨论内容 | 关键信息 | 相关资源 |
|------|----------|----------|----------|
| 2026-05-11 | PBR功能概述 | 理解PBR核心概念和应用场景 | 厂商文档 |

## 切换命令
- **切换到话题**：`Switch to switch-pbr-analysis`
- **保存话题**：`Save switch-pbr-analysis workbench`
- **结束话题**：`End switch-pbr-analysis topic`

## 版本控制
- **当前版本**：v1.0
- **版本历史**：
  - v1.0 (2026-05-11)：初始版本，涵盖PBR基础、IPv4/IPv6对比、双栈策略

---

**工作台版本**：v1.0  
**创建时间**：2026-05-11  
**最后更新**：2026-05-11