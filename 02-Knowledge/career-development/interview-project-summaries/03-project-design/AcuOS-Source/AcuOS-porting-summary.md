# AcuOS RTOS 移植总结（ARM M4 ↔ SHARC DSP）

> 自研 RTOS 跨平台移植的完整总结，基于 AcuOS-Source 两个平台的实际源码。
> 一句话：**RTOS 移植 = 改「平台相关层」，保留「平台无关层」**。

## 一、两个平台的源码结构对比

| 平台 | 文件 | 上下文切换汇编量 | 日期 |
|------|------|-----------------|------|
| **ARM M4** | `AcuOs.h` + `AcuOsCore.c` + `AcuOsCpu.s` | ~110 行 | 2018-08 |
| **SHARC DSP** | `AcuOs.h` + `AcuOsCoreDsp.c` + `AcuOsAlarm.c` + `SharcDsp.c` + `SharcDspAsm.asm` + `SharcDspAsm.h` | ~1000 行 | 2021-01 |

> 同名文件 `AcuOs.h`（内核 API）两边一致；`.s`（ARM 汇编）vs `.asm`（SHARC 汇编）是两套完全不同的平台相关代码。

## 二、RTOS移植必须改的 7 件事

### 1. 上下文切换汇编（最核心，工作量最大）

| | ARM M4（`AcuOsCpu.s`） | SHARC DSP（`SharcDspAsm.asm`） |
|---|---|---|
| 代码量 | ~110 行 | **~1000 行** |
| 保存寄存器 | 只手动存 R4-R11；R0-R3/R12/LR/PC/xPSR 由**硬件自动压栈** | **全部手动**：DAG 寄存器(I/L/B/M ×16)、数据 R0-15、S0-15(40bit)、乘法器 MR、循环栈、PC 栈、状态栈、位 FIFO |
| 切换机制 | PendSV 异常，MSP/PSP 双栈 | MODE1 切换前台/后台寄存器组 |
| 额外坑 | 无 | 一堆芯片 **anomaly workaround**（`WA_15000004`/`WA_20000081`/`WA_20000069`…） |

**为什么差异这么大**：Cortex-M 有硬件上下文自动保存（异常入栈），SHARC 没有，所有寄存器都要软件手动搬；且 SHARC 的 40-bit 数据寄存器、循环栈（loop stack）、PC 栈（PCSTK）、状态栈（STS）这些 ARM 根本没有。

### 2. 开关中断 / 进入临界区

```asm
; ARM M4：PRIMASK + CPSID/CPSIE
OsEnterCritical:
    MRS  R0, PRIMASK
    CPSID I
    BX   LR

; SHARC：MODE1 的 IRPTEN 位
BIT SET MODE1 MODE1_INT_EN_BIT;   ; 开中断
BIT CLR MODE1 MODE1_INT_EN_BIT;   ; 关中断
```

### 3. 触发上下文切换的中断源

```c
// ARM：触发 PendSV
NVIC_INT_CTRL = NVIC_PENDSV_SET;

// SHARC：SFT31 软件中断，或 SEC（系统事件控制器）中断
// 源码含 anomaly 36-10-0101 workaround：用 SEC 中断而非核心中断
```

### 4. 任务栈初始化

```c
// ARM M4（AcuOsCore.c 的 OsTaskStkInit）：
// 按"异常入栈帧"格式填：xPSR/PC/LR/R12/R3-R0 + R4-R11
*(puiStk)   = 0x01000000u;   // xPSR（Thumb 位）
*(--puiStk) = (Uint32)pTask; // PC
...

// SHARC：按 ContextRecord 结构填，寄存器布局完全不同
// 栈指针是 I7，字寻址（word addressing）
```

### 5. 栈指针 / 寄存器模型

- ARM M4：MSP（主栈，中断用）/ PSP（进程栈，任务用），双栈自动切换
- SHARC：前台/后台寄存器组，通过 MODE1 位切换，I7 做栈指针

### 6. Tick 定时器

- ARM：SysTick（`SysTick_Handler` 里调 `OsTimeTick`）
- SHARC：不同的定时器外设

### 7. 编译器和汇编语法

- ARM：Keil/GCC，`.s` 文件，Thumb 指令
- SHARC：ADI CrossCore，`.asm` 文件，`.SECTION`/`.import`/`.extern` 语法完全另一套

## 三、平台无关层（两边复用不改）

从源码看，以下纯 C 逻辑两边一致，移植时直接复用：

- `OsSchedule` / `OsPreSchedule`：遍历找最高优先级就绪任务
- `OsTimeTick` / `OsTimeDly`：延时递减、tick 处理
- Sem / Queue / Flag / Mutex 的 Create / Post / Pend：状态机逻辑
- TCB、事件、队列的抽象数据结构

## 四、两个版本的功能差异（DSP 版更完善）

| 维度 | ARM M4 版 | SHARC DSP 版 |
|------|-----------|--------------|
| TCB 组织 | 静态数组 `g_atOsTaskTcbTable[OS_MAX_TASKS]` | **链表** `g_ptOsTaskTcbTableHead` + `ptNext` |
| IPC 种类 | Sem + Queue（2 种） | Sem + Queue + Flag + Mutex（4 种） |
| 定时器 | 无 | ✅ Timer（周期/单次） |
| 软件时钟 | 无 | ✅ RTC 时间转换（秒 ↔ 年月日时分秒） |
| 栈溢出检测 | 无 | ✅ `OsTaskStkCheck`（遍历检查栈底 0 值） |
| 系统时钟 | tick 计数 | tick + ms + sec + 运行时长 |

## 五、关键数据

| | ARM M4 版 | SHARC DSP 版 |
|---|-----------|--------------|
| 内核大小 | ~5KB | ~10KB |
| 单任务栈 | ~256B | ~800B（TCB 36B + 栈） |
| IPC | Sem/Queue | Mutex/Flag/Alarm 全支持 |

## 六、面试话术（背）

> "RTOS 移植我分两层：平台无关层（调度器、IPC、时间管理）直接复用，平台相关层重写。最核心的是**上下文切换汇编**——ARM M4 上 PendSV + 硬件自动压栈，我只手动存 R4-R11，一百行搞定；但移植到 SHARC DSP 时，没有硬件自动压栈，所有寄存器（DAG、40-bit 数据、乘法器、循环栈、PC 栈）都要手动保存恢复，还踩了一堆芯片 anomaly，汇编写了上千行。其次是开关中断、触发切换的中断源、任务栈初始化、tick 定时器，每个平台都不一样。"

**一句话总结**：移植改 7 件事，**上下文切换汇编最重**——平台有没有硬件上下文保存（Cortex-M 有、SHARC 没有），直接决定移植工作量是 100 行还是 1000 行。
