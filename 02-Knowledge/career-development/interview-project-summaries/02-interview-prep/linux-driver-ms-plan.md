# Linux 驱动 MS 学习计划（配合 H3C 平台）

> 触发：2026-09-24 用户决定补 Linux 通用知识（正在 H3C Marvell+Linux 平台学习）
> 依据：2026 年 Linux 驱动岗高频考点（已搜索核对）+ 你的方向（Linux 驱动/固件，C 语言，已实操 DTS/GPIO 中断/字符设备）
> 目标：6 周把 Linux 驱动八大模块学透，每个都「读 H3C 平台代码 + 用本质→实践→坑讲一遍」，既补 V2 简历又能 MS 讲
> ⚠️ 全用 C，不碰 C++；只学驱动/固件要的，不碰应用层花活

---

## 一、MS 高频考点地图（2026 已核对）

驱动岗 MS 真正想考察三件事（来自 2026 面经趋势）：①能否从硬件寄存器打通到应用层（系统思维）②真实项目踩过多少坑（方法论）③面对 AI/异构是否跟得上。考点集中在：

| 模块 | 频率 | 5 年以上还会深挖 |
|:--|:--|:--|
| 字符设备驱动框架 | 极高 | 框架设计取舍、probe 全流程 |
| 设备树 DTS | 极高 | 设备树匹配机制、中断/时钟描述 |
| 中断（上下半部） | 极高 | 为什么中断不能睡眠、下半部选型 |
| 并发与同步 | 高 | spinlock vs mutex 使用边界、死锁排查 |
| 内存管理 / DMA | 高 | kmalloc vs vmalloc、DMA 一致性 |
| 平台驱动模型 | 高 | probe/remove、of_match_table |
| 启动流程 | 中 | initcall 层级、设备树解析时机 |
| 系统编程（应用层） | 中 | IO 多路复用、多线程同步 |

---

## 二、八大模块：考点 + H3C 平台实操 + MS 答法

> 每模块结构：核心考点 → H3C 平台哪里能找到对应 → MS 用「本质→实践→坑」答（呼应 senior-narrative-arsenal）

### 模块 1：字符设备驱动框架（Week 1）
- **核心考点**：`file_operations`（open/read/write/ioctl/release）、`register_chrdev`/`alloc_chrdev_region`/`cdev_init`/`cdev_add`、主/次设备号、`copy_to_user`/`copy_from_user`
- **H3C 实操**：在 TSN 交换机找一个你调过的字符设备驱动，读它的 `file_operations` 注册和 `ioctl` 分发
- **MS 答法**：本质（字符设备 = 把硬件抽象成文件，应用层用 open/read/write 操作）→ 实践（我在 X 驱动里实现了 file_operations 的 read/ioctl，应用层通过 /dev/xxx 访问）→ 坑（copy_to_user 没检查返回值导致数据没考出去 / 设备号冲突）

### 模块 2：设备树 DTS（Week 2）
- **核心考点**：节点/属性（`compatible`/`reg`/`interrupts`/`clocks`/`gpios`）、DTS 如何匹配驱动（compatible → of_match_table → probe）、中断描述（`interrupts`/`interrupt-parent`/`#interrupt-cells`）
- **H3C 实操**：读 TSN 的 PHY/MAC 节点的 DTS（reg 地址、interrupts、clocks），看你配的 GPIO 中断在 DTS 里怎么写
- **MS 答法**：本质（DTS = 把硬件描述从内核代码里抽出来，改硬件不改代码）→ 实践（我给 PHY 配过 reg/interrupts，驱动 of_match_table 靠 compatible 匹配进 probe）→ 坑（interrupts 触发方式写错导致中断不触发 / 忘记 #interrupt-cells）

### 模块 3：中断（上下半部）（Week 3）
- **核心考点**：`request_irq`/`free_irq`、上半部（硬中断，快进快出）vs 下半部（软中断/tasklet/工作队列/线程化中断）、为什么中断里不能睡眠
- **H3C 实操**：看你调的 GPIO 中断 / SyncE 中断，request_irq 怎么注册，耗时操作放哪个下半部
- **MS 答法**：本质（上半部抢时间、下半部干重活）→ 实践（我的 GPIO 中断上半部只清标志，解析放工作队列）→ 坑（中断里用了 mutex/printk 导致睡眠死锁——中断上下文不能用会睡眠的锁）

### 模块 4：并发与同步（Week 4）
- **核心考点**：自旋锁 spinlock（原子上下文、不可睡眠）vs 互斥锁 mutex（可睡眠）、原子操作 atomic_t、死锁、竞态
- **H3C 实操**：在驱动里找一个共享资源（寄存器/缓冲区）的保护，看用的是 spinlock 还是 mutex，为什么
- **MS 答法**：本质（锁是为了保护共享数据，选哪种看上下文能否睡眠）→ 实践（中断里用 spinlock_irqsave，进程上下文用 mutex）→ 坑（中断里用 mutex 死锁 / 锁粒度太大影响性能）——可呼应你 RTOS 的信号量/临界区经验

### 模块 5：内存管理 / DMA（Week 5）
- **核心考点**：kmalloc（物理连续）vs vmalloc（仅虚拟连续）、`dma_alloc_coherent`（一致性映射）vs `dma_map_single`（流式映射）、Cache 一致性
- **H3C 实操**：看 MAC/PHY 的 DMA 描述符环怎么分配（dma_alloc_coherent），DMA 缓冲区怎么和 Cache 同步
- **MS 答法**：本质（DMA 要物理地址且要处理 CPU Cache 与内存一致性）→ 实践（描述符环用 dma_alloc_coherent 保证物理连续 + 不被 Cache 坑）→ 坑（DMA 后 CPU 读到 Cache 旧数据，和你 DSP 的 DMA-Cache 一致性经验完全相通）

### 模块 6：平台驱动模型（Week 6）
- **核心考点**：`platform_driver`/`platform_device`、`probe`/`remove`、`of_match_table`、设备树节点如何触发 probe
- **H3C 实操**：读一个 platform 驱动的 probe 函数，看资源（reg/irq）怎么从 DTS 拿到
- **MS 答法**：本质（platform 总线把「设备」和「驱动」解耦，设备树供设备、驱动供操作）→ 实践（我的 X 驱动是 platform_driver，probe 里 of_property 读 DTS、devm_request_irq）→ 坑（devm_ 资源管理没用对导致泄漏）

### 模块 7：启动流程（串讲）
- **核心考点**：Bootloader（U-Boot）→ 内核解压 → start_kernel → 设备树解析 → initcall 层级（core/postcore/arch/subsys/device/module）→ 驱动初始化
- **H3C 实操**：dmesg 看启动日志，找你驱动的 initcall 打印，理解它在哪一级初始化
- **MS 答法**：本质（内核按 initcall 层级分批初始化，设备树在 start_kernel 早期解析）→ 实践（我驱动用 module_init（device 级），dmesg 能看到 probe 时机）→ 坑（依赖的设备没先初始化导致 probe defer）

### 模块 8：系统编程 / 应用层（你已有基础，快速过）
- **核心考点**：IO 多路复用（select/poll/epoll 区别）、多线程 pthread + 互斥/条件变量、进程间通信
- **H3C 实操**：你在 TSN 应用层的多线程/socket 经验直接讲
- **MS 答法**：重点背 epoll 为什么比 select/poll 高效（O(1) 事件通知 vs O(n) 轮询）

---

## 三、6 周学习计划（边工作边学，每周 1 模块）

| 周 | 模块 | 动作 |
|:--|:--|:--|
| W1 | 字符设备框架 | 读 H3C 一个字符设备驱动 + 讲一遍 + 写要点 |
| W2 | 设备树 DTS | 读 TSN PHY/MAC/GPIO 中断的 DTS 节点 + 讲一遍 |
| W3 | 中断上下半部 | 读 GPIO/SyncE 中断注册 + 下半部 + 讲一遍 |
| W4 | 并发同步 | 找一个驱动的 spinlock/mutex 用法 + 对比 RTOS 信号量讲一遍 |
| W5 | 内存/DMA | 读 MAC DMA 描述符 + dma_alloc_coherent + 对比 DSP DMA-Cache 讲一遍 |
| W6 | 平台驱动 + 启动 + 应用层 | 读 platform probe + dmesg 启动日志 + 串讲 |

**每周末铁律**：把本周模块用「本质一句话 → H3C 实践 → 踩的坑」写 3 行，能脱口而出——这既补 V2 简历素材，又是 MS 答法。

---

## 四、自检清单（6 周末自测）

- [ ] 能手画字符设备驱动注册流程（register_chrdev → file_operations → /dev 节点）
- [ ] 能讲 DTS 的 compatible 怎么匹配到 probe
- [ ] 能讲中断为什么不能睡眠 + 上下半部怎么分工
- [ ] 能讲 spinlock vs mutex 的使用边界（中断 vs 进程上下文）
- [ ] 能讲 kmalloc vs vmalloc + DMA 为什么要 dma_alloc_coherent
- [ ] 能讲 platform 驱动 probe 时机 + initcall 层级
- [ ] 每个模块都有 1 个 H3C 平台的真实例子 + 1 个坑

---

## 关联

- [[../../01-company-interviews/resume-optimized|V2 Linux 驱动简历]] — 本计划补的就是这份简历的核心能力
- [[../senior-narrative-arsenal|资深叙事弹药库]] — 「本质→实践→坑」答法模板
- [[../dsp-algorithm-review|DSP 算法深度复习]] — DMA-Cache 一致性（和模块 5 相通）

---

**最后更新**: 2026-09-24
