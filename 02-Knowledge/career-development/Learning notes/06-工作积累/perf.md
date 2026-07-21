# Linux perf 与火焰图 —— 嵌入式开发者从零上手手册

> **适用对象**：有 MCU / RTOS 背景、但没接触过 Linux 性能分析的嵌入式工程师
> **目标**：搞懂 perf 是什么、能解决什么问题、怎么在开发/调试中用起来
> **一句话**：perf 是 Linux 自带的"软件示波器 + 逻辑分析仪"，火焰图是把它的数据画成"哪里最耗时"的一张图。

---

## 一、perf 到底是干嘛的？

`perf` 是 Linux 内核自带的一套**性能分析工具**（底层是内核的 `perf_event` 子系统），不需要额外驱动，装好就能用。

**核心原理 —— 采样（Sampling）：**
perf 周期性地（比如每 99 次 CPU 时钟周期、或每次缓存未命中）"打断"正在跑的程序，记录下：
- 当前在哪个函数（`PC` 程序计数器）
- 当前的调用栈（是谁调用了它）

采样攒够几万次后，统计"哪个函数被采到的次数最多" → 次数多 = 占用 CPU 时间多 = 热点。

> **和 MCU 调试的类比**（你最熟的思路）：
> | 你想知道的事 | MCU / RTOS 的做法 | Linux 里 perf 的做法 |
> |:-------------|:------------------|:---------------------|
> | 这段函数跑了多久 | DWT 周期计数器 / 翻转 GPIO + 示波器 | `perf stat` 统计 cycles |
> | 谁在吃 CPU | 逻辑分析仪抓总线 / ITM 跟踪 | `perf top` 实时看占用最高的函数 |
> | 调用关系 | 单步调试看调用栈 | `perf record -g` 采样调用栈 |
> | 为什么慢 | 猜 + 打点计时 | 火焰图直接画出来 |

**关键认知**：perf 不是"单步调试器"（那是 gdb），它不暂停程序，而是"边跑边抽样"，所以**对程序运行影响极小（通常 < 5%）**，适合分析真实运行中的性能问题。

---

## 二、它能解决哪些实际问题？

| 你遇到的现象 | perf 怎么帮你 |
|:-------------|:--------------|
| 程序 CPU 占用 100%，不知道卡在哪 | `perf top` 实时看到占用最高的函数名 |
| 整体慢，但不知道瓶颈是算法还是 IO | `perf stat` 看 cycles / cache-miss / 上下文切换比例，判断是 CPU 密集还是 IO 密集 |
| 某函数明明简单却很慢 | 火焰图看到它被**调用了几万次**（调用频率问题，不是单次慢） |
| 启动慢、开机慢 | 全系统采样 10 秒，火焰图一眼看出启动链路热点 |
| 缓存命中率低、分支预测失败多 | `perf stat` 直接出 `cache-misses`、`branch-misses` 计数 |
| 想知道内核在干嘛（中断/调度/系统调用） | `perf record -e sched:*` 跟踪调度，`perf trace` 看系统调用 |

**最适合 perf 的场景**：嵌入式 Linux 应用卡顿、CPU 占用高、功耗高（CPU 一直跑满）、启动慢、算法优化前后对比。

> ⚠️ **不适合 perf 的场景**：纯裸机 MCU（无 Linux 内核）。裸机请用 ETM/ITM 硬件跟踪、DWT 周期计数、逻辑分析仪。perf 只对**跑 Linux 的平台**（嵌入式 Linux 板子如 i.MX、RK3399、全志，或 x86 开发机）有效。

---

## 三、火焰图（Flame Graph）是什么？

火焰图是 Brendan Gregg 发明的、**把 perf 采样数据可视化**的一张 SVG 图。

```
    main                         ← 最顶层是调用入口
    ├── process_data            ← 中间是调用链
    │   ├── parse_json          ← 越往下越底层
    │   │   └── memcpy ▆▆▆▆▆▆▆▆  ← 方块越宽 = 采样越多 = 越耗时（热点！）
    │   └── encode
    └── log_write
```

| 维度 | 含义 |
|:------|:-----|
| **横轴** | 采样数量（≈ 占用 CPU 的时间比例），**不代表时间先后**，只代表"谁占比大" |
| **纵轴** | 调用栈深度（越上面是调用者，越下面是被调用的底层函数） |
| **方块宽度** | 该函数及其子函数占用的 CPU 比例，越宽越热 |
| **颜色** | 默认随机，无特殊含义（也可按模块染色） |

**怎么看**：从最宽的方块往上看它的调用链，那个最宽的函数就是你要优化的热点。点一下还能展开看细节。

---

## 四、怎么安装

**x86 / 开发机（Ubuntu/Debian）：**
```bash
sudo apt install linux-tools-common linux-tools-$(uname -r)
# 验证
perf --version
```

**嵌入式目标板（关键）：**
- 内核必须打开 `CONFIG_PERF_EVENTS=y`（一般默认开）
- 通过 Buildroot / Yocto 选上 `perf` 包，或交叉编译 `linux/tools/perf`
- 板子文件系统里要有 `perf` 可执行文件，且 `/proc/sys/kernel/perf_event_paranoid` 权限够（调试时可临时设为 -1）

```bash
# 板子上检查内核是否支持
cat /proc/sys/kernel/perf_event_paranoid   # 数值越小权限越宽，1 或 -1 可用
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid   # 临时放开（调试用）
```

**火焰图工具（生成 SVG 用）：**
```bash
git clone https://github.com/brendangregg/FlameGraph.git
# 里面 stackcollapse-perf.pl 和 flamegraph.pl 就是生成脚本
```

---

## 五、基本使用流程（5 步上手）

> 前置：你的程序编译时**必须带 `-g` 且不要 strip**，否则 perf 只能看到地址看不到函数名。

```bash
# ① 先宏观看指标（不采样，直接计数）
perf stat ./your_program
#   输出：任务耗时、cycles、instructions、cache-misses、分支预测失败率
#   看 CPI（cycles/instructions），>2 说明指令效率低，可能 cache 差或分支差

# ② 采样调用栈（记录到 perf.data）
perf record -g -F 99 ./your_program        # -g 采调用栈，-F 99 每秒采样99次
#   或针对已运行进程：
perf record -g -p <PID> -- sleep 30        # 采 30 秒
#   或全系统：
perf record -a -g -F 99 -- sleep 10        # 整机采样 10 秒

# ③ 交互式看报告
perf report                               # 按占用排序的函数列表，方向键浏览

# ④ 实时看谁占 CPU（类似 top，但显示函数名）
perf top

# ⑤ 生成火焰图
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > out.svg
#   用浏览器打开 out.svg 即可
```

**分析闭环（开发时反复用）：**
```
perf stat 看大体指标 → 发现慢 → perf record + 火焰图定位热点函数
   → 改代码优化 → 再 perf stat 对比数字 → 确认提升
```

---

## 六、嵌入式开发中的特殊用法

### 6.1 在目标板上采，回主机分析（最常见）
板子性能弱、没图形界面，所以：
1. **板子上** `perf record -g ./app` 生成 `perf.data`
2. 把 `perf.data` 和**带符号的二进制/app**（或 vmlinux）拷回 x86 开发机
3. **开发机上**用对应架构的 `perf` + 火焰图工具生成 SVG

> 注意：跨架构（ARM 板 → x86 机）分析时，开发机上的 `perf` 要能识别 ARM 的符号；最简单的是在板子上完成 `perf script`，把文本结果传回主机只做画图。

### 6.2 内核态 + 用户态一起看
```bash
perf record -g -e cycles:u -e cycles:k ./app   # 分别采用户态/内核态 cycles
```
嵌入式常见问题：应用慢其实是内核驱动/系统调用耗时的（比如频繁 `copy_to_user`、中断太频繁），火焰图能同时显示内核栈。

### 6.3 跟踪特定事件（不只是 CPU）
```bash
perf stat -e cache-misses,branch-misses,context-switches ./app   # 只看这几个事件
perf record -e sched:sched_switch -a -- sleep 5                  # 跟踪任务切换
perf trace -p <PID>                                             # 类似 strace，看系统调用耗时
```

### 6.4 动态插桩（不用改代码）
```bash
# 在内核函数或用户函数动态埋点（类似软件断点，但只计数不打断）
perf probe -x ./app my_function
perf record -e probe_app:my_function ./app
```

---

## 七、常见坑（必看）

| 坑 | 现象 | 解决 |
|:---|:-----|:-----|
| **看不到函数名** | 报告里全是十六进制地址 | 编译加 `-g`，发布前别 `strip`，保留符号表 |
| **内核函数看不到** | 只有 `[unknown]` | 内核需开 `CONFIG_FRAME_POINTER=y`，并提供 `vmlinux` |
| **采样频率太高** | 程序明显变慢、数据失真 | 默认 `-F 99` 即可，别用过高频率 |
| **权限不够** | `perf_event_open() failed` | 调 `perf_event_paranoid` 为 -1，或加 `sudo` |
| **短程序采不到** | 火焰图空 | 延长采集时间（`sleep 30`），或循环跑多次再采 |
| **容器/嵌入式受限** | 部分事件不可用 | 用软件事件（context-switches/page-faults）替代硬件事件 |
| **栈被优化掉** | 调用链断裂、扁平 | 编译加 `-fno-omit-frame-pointer` |

### 7.1 坑位详解：这两个编译选项加在哪、何时加

上面表格里第 173 行（`-g` / `strip`）和第 179 行（`-fno-omit-frame-pointer`）说的都是**编译/链接阶段给编译器加的 flag**，不是改 perf 命令、也不是改运行参数。

#### `-g` 与 `strip`（对应「看不到函数名」）

- **加哪里**：编译/链接命令里（Makefile 的 `CFLAGS`、CMake 编译选项、或直接 `gcc ...`）。
  ```bash
  gcc -g app.c -o app          # ← -g 加在这里
  ```
- **作用**：`-g` 把**调试符号（函数名、行号、DWARF 信息）**塞进生成的 ELF。
- **`strip` 是反向操作**：编译完成后执行 `strip app` 会把符号表删掉。「发布前别 strip」= 用 perf 分析时**别执行 strip**，让符号留在二进制里。
- **何时加**：
  - 开发 / 调试 / 性能分析阶段：加 `-g`、不 strip → perf 才能显示函数名。
  - 产品发布：可 strip 减小体积；但要做性能分析时，必须用**带符号版本**（保留一份 unstripped 副本即可）。
- **类比 MCU**：和 J-Link/GDB 调 STM32 一个道理——编译加 `-g` 生成带符号 `.elf`，调试器才能把地址对应到源码行；`-g` 就是给「调试器/perf」看的地图，`strip` 是把地图撕掉。

#### `-fno-omit-frame-pointer`（对应「栈被优化掉」）

- **加哪里**：同样在编译命令里，常与 `-g` 一起。
  ```bash
  gcc -g -fno-omit-frame-pointer app.c -o app
  ```
- **作用**：开优化（`-O2` 及以上）时，编译器默认**省略帧指针（frame pointer）**，把 BP 寄存器省下来做通用寄存器。但 perf 靠**帧指针顺着调用栈回溯**，才能画出火焰图的「层级」（谁调用谁）。省略后 → 火焰图变「扁平的一条」，只有函数名没有层级。此选项**强制保留帧指针**，让 perf 能展开调用栈。
- **何时加**：只要你想用 `perf record -g` 看**调用链 / 火焰图层级**，且编译开了优化（`-O2` 等），就加它。若用 `-O0`（Debug 默认），本身不省略帧指针，可不加。

#### 构建系统里直接抄

```makefile
# Makefile
CFLAGS += -g -fno-omit-frame-pointer
```

```cmake
# CMakeLists.txt
add_compile_options(-g -fno-omit-frame-pointer)
# 或简单用 Debug 构建类型（自带 -g，开了 -O2 时再补 -fno-omit-frame-pointer）
set(CMAKE_BUILD_TYPE Debug)
```

#### 两句话记住分工

| flag | 解决什么 | 不加的后果 |
|:-----|:---------|:-----------|
| `-g` | 让 perf 知道**地址→函数名**（符号表） | 报告全是一串十六进制地址 |
| `-fno-omit-frame-pointer` | 让 perf 能**展开调用栈层级** | 火焰图扁平、调用链断裂 |
| `strip`（别做） | 反向操作，删掉上面的符号 | 等于白加 `-g` |

---

## 八、perf 事件速查

| 事件 | 含义 | 用来判断什么 |
|:-----|:-----|:-------------|
| `cycles` | CPU 时钟周期 | 总工作量 |
| `instructions` | 执行的指令数 | 配合 cycles 算 CPI |
| `cache-references` / `cache-misses` | 缓存访问 / 未命中 | 命中率低 → 内存访问模式差 |
| `branch-misses` | 分支预测失败 | 高 → 有不好预测的分支（如大量 if 随机） |
| `context-switches` | 上下文切换 | 高 → 任务切换频繁、可能锁竞争 |
| `page-faults` | 缺页 | 高 → 内存分配/访问异常 |
| `cpu-clock` | CPU 时间 | 不依赖硬件 PMU，通用 |

---

## 九、和 MCU 调试手段的对照总结

| 目标 | MCU / RTOS 手段 | Linux perf 手段 |
|:------|:----------------|:----------------|
| 测单段代码耗时 | DWT CYCCNT / GPIO+示波器 | `perf stat` / `perf probe` |
| 找全局热点 | 手动打点计时（挨个测） | `perf top` / 火焰图（全自动） |
| 看调用关系 | 单步 / 静态看代码 | `perf record -g` 采样调用栈 |
| 看缓存/分支效率 | 无（MCU 少见） | `cache-misses` / `branch-misses` 计数 |
| 看内核/驱动耗时 | 无（裸机无 OS） | `cycles:k` 内核态采样 |
| 实时观察 | 逻辑分析仪 | `perf top` 实时 |

> **核心差异**：MCU 靠"硬件调试口 + 手动打点"，perf 靠"内核子系统 + 自动采样"。perf 让你**不改一行代码、不暂停程序**就能拿到全系统的热点图——这正是嵌入式 Linux 工程师替代"示波器大法"的现代做法。

---

## 十、最小上手清单（完全不懂也能照做）

| # | 动作 | 命令 |
|:--|:-----|:-----|
| 1 | 装 perf | `sudo apt install linux-tools-common linux-tools-$(uname -r)` |
| 2 | 编译带符号 | `gcc -g -fno-omit-frame-pointer your_app.c -o your_app` |
| 3 | 看大指标 | `perf stat ./your_app` |
| 4 | 采调用栈 | `perf record -g -F 99 ./your_app` |
| 5 | 看热点 | `perf report`（或生成火焰图 `perf script \| stackcollapse-perf.pl \| flamegraph.pl > out.svg`） |

> 记住一句口诀：**stat 看大概，record 抓细节，report/火焰图 找热点，优化后再 stat 对比数字。**
