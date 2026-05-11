# 交换机 PBR（策略路由）

> **日期**：2026-05-11
> **状态**：已完成
> **知识点**：策略路由原理、IPv4/IPv6对比、双栈配置、H3C Comware配置

---

## 一、PBR 是什么

**PBR（Policy-Based Routing）**：基于策略的路由选择，不依赖目的IP做路由决策，而是根据预定义的条件（源IP、协议、端口、DSCP等）决定转发路径。

**核心价值**：
- 流量工程：优化路径、提高带宽利用率
- 负载均衡：分散流量到多条链路
- QoS：为关键业务保障路径
- 安全策略：流量隔离、引导到安全设备

---

## 二、PBR 工作三要素

```
1. 匹配条件（Match）：ACL定义流量分类规则
2. 操作动作（Apply）：定义匹配后的转发行为
3. 应用位置：在接口上绑定策略
```

| 要素 | 可选项 |
|------|--------|
| **匹配条件** | 源/目的IP、协议类型、端口号、DSCP/TOS |
| **操作动作** | 设置下一跳、设置出接口、设置优先级、标记流量 |
| **应用位置** | 接口入方向 |

---

## 三、典型应用场景

| 场景 | 描述 | 典型配置方式 |
|------|------|------------|
| 负载均衡 | 不同来源流量走不同出口 | 基于源IP的PBR |
| 链路备份 | 主链路故障自动切换 | 多下一跳 + 优先级 |
| 服务质量 | 关键业务走高优先级路径 | 基于DSCP的PBR |
| 流量分离 | 特定流量引导到防火墙等设备 | 基于协议/端口 |
| 多ISP接入 | 不同业务走不同ISP | 基于目的端口 |

---

## 四、IPv4 vs IPv6 PBR 对比

| 对比项 | IPv4 PBR | IPv6 PBR |
|--------|----------|----------|
| **ACL类型** | `acl advanced` | `acl ipv6 advanced` |
| **地址格式** | 32位点分十进制 | 128位十六进制 |
| **策略命令** | `policy-based-route` | `ipv6 policy-based-route` |
| **下一跳** | `apply next-hop` | `apply next-hop` |
| **接口应用** | `ip policy-based-route` | `ipv6 policy-based-route` |
| **优先级字段** | IP Precedence/TOS | Traffic Class/Flow Label |
| **查看命令** | `display ip policy-based-route` | `display ipv6 policy-based-route` |

---

## 五、双栈环境 PBR 策略

### 配置原则
1. **独立配置**：IPv4和IPv6 PBR需分别配置
2. **策略协调**：确保两种协议的策略逻辑一致
3. **资源管理**：注意ACL和策略的资源占用

### 典型场景
- **协议感知路由**：根据IP协议版本选择不同路径
- **双栈负载均衡**：同时利用IPv4和IPv6链路
- **故障切换**：一种协议路径故障时，另一种提供备份

---

## 六、H3C Comware V7/V9 配置示例

> V7和V9基础PBR命令一致，V9增强SRv6策略路由等高级特性。

### IPv4 PBR
```bash
# 1. 定义ACL匹配流量
acl advanced 3000
 rule 0 permit ip source 192.168.1.0 0.0.0.255

# 2. 创建策略路由
policy-based-route PBR-EXAMPLE permit node 10
 if-match acl 3000
 apply next-hop 10.1.1.1

# 3. 接口上应用
interface GigabitEthernet1/0/1
 ip address 192.168.1.1 255.255.255.0
 ip policy-based-route PBR-EXAMPLE
```

### IPv6 PBR
```bash
acl ipv6 advanced 3000
 rule 0 permit ipv6 source 2001:db8::/32

ipv6 policy-based-route PBR-IPv6-EXAMPLE permit node 10
 if-match acl ipv6 3000
 apply next-hop 2001:db8::1

interface GigabitEthernet1/0/1
 ipv6 address 2001:db8::1/64
 ipv6 policy-based-route PBR-IPv6-EXAMPLE
```

### 高级配置
```bash
# 多下一跳（负载分担/备份）
policy-based-route PBR-REDUNDANT permit node 10
 if-match acl 3000
 apply next-hop 10.1.1.1
 apply next-hop 10.1.2.1

# 默认下一跳（无精确路由时生效）
policy-based-route PBR-DEFAULT permit node 10
 if-match acl 3000
 apply default-next-hop 10.1.1.1

# 设置出接口（点对点链路）
policy-based-route PBR-INTERFACE permit node 10
 if-match acl 3000
 apply output-interface GigabitEthernet1/0/2
```

### V9 增强特性（V7不支持）
```bash
# SRv6策略路由
# ipv6 policy-based-route PBR-SRv6 permit node 10
#  if-match acl ipv6 3000
#  apply srv6-policy endpoint 2001:db8::1
```

### 验证命令
```bash
display ip policy-based-route
display ipv6 policy-based-route
display ip policy-based-route interface GigabitEthernet1/0/1
```

---

## 七、注意事项

1. **策略冲突**：多个PBR策略注意优先级
2. **性能影响**：复杂匹配条件影响转发性能
3. **维护复杂度**：策略越多维护越难
4. **故障排查**：PBR可能隐藏传统路由问题

---

## 关键概念速查

| 概念 | 一句话解释 |
|------|-----------|
| **PBR** | 基于策略（而非目的IP）的路由选择 |
| **policy-based-route** | H3C策略路由配置命令 |
| **if-match** | 匹配条件子句 |
| **apply** | 执行动作子句 |
| **next-hop** | 设置下一跳地址 |
| **default-next-hop** | 默认下一跳（仅无精确路由时生效） |
| **output-interface** | 设置出接口 |

---

**详细笔记**：`workbench/topics/switch-pbr-analysis.md`
