---
title: ARM Cortex Microcontrollers 使用说明（嵌入式固件专家）
name: arm-cortex-microcontrollers
description: 当用户要编写/调试 ARM Cortex-M 微控制器（Teensy 4.x、STM32 F4/F7/H7、nRF52、SAMD）的固件、外设驱动（I2C/SPI/UART/ADC/DAC/PWM/USB/CAN）、DMA 与缓存一致性、内存屏障、中断优先级、临界区、Hardfault 调试、栈溢出保护，或做 TFLM 在 MCU 上的部署实践时使用。
source: "https://github.com/wshobson/agents/tree/main/plugins/arm-cortex-microcontrollers"
tags:
  - embedded
  - cortex-m
  - firmware
  - driver
  - dma
  - memory-safety
created: 2026-08-21
---

# ARM Cortex Microcontrollers 使用说明

> **项目来源**：[wshobson/agents](https://github.com/wshobson/agents/tree/main/plugins/arm-cortex-microcontrollers)（MIT，质量评分 100/100）
> **核心 agent**：`arm-cortex-expert`（本体见 [[SKILL]]）
> **收录日期**：2026-08-21

## 一句话说明

一个面向 **ARM Cortex-M 微控制器**的固件开发专家知识库 + 工作流，核心是"写出可靠、安全、可维护的嵌入式代码"——尤其聚焦 Cortex-M7 的**内存屏障、DMA/缓存一致性**这些最容易踩坑的底层模式。

## 目标平台

| 平台 | 内核 | 典型应用 |
|:-----|:-----|:---------|
| Teensy 4.x | Cortex-M7（i.MX RT1062, 600MHz） | 高性能 + TCM + 缓存 + DMA |
| STM32 F4/F7/H7 | Cortex-M4/M7 | HAL/LL + CubeMX |
| nRF52 | Cortex-M4 | BLE + nRF SDK/Zephyr |
| SAMD | Cortex-M0+/M4 | Arduino/裸寄存器 |

## 核心能力（9 大板块）

| # | 板块 | 内容 | 对应你的场景 |
|:--|:-----|:-----|:-------------|
| 1 | 外设驱动 | I2C/SPI/UART/ADC/DAC/PWM/USB/CAN/SDIO，HAL 与裸寄存器 | 8 年嵌入式经验直接对口 |
| 2 | 内存屏障 | M7 弱序内存，`__DMB()`/`__DSB()` 封装 mmio 读写 | TFLM 底层寄存器操作 |
| 3 | DMA + 缓存一致性 | 32 字节对齐、DTCM 放置、cache maintenance | TFLM 音频/传感器数据搬运 |
| 4 | 中断优先级 | NVIC 配置、优先级分组、预留原则 | 实时性约束 |
| 5 | 临界区 | BASEPRI vs PRIMASK、保持临界区短 | 共享数据保护 |
| 6 | Hardfault 调试 | HFSR/CFSR/MMFAR/BFAR 定位 | 现场疑难 bug 排查 |
| 7 | 栈溢出保护 | MPU guard + canary + watchdog | 嵌入式内存安全 |
| 8 | FPU 上下文 | lazy stacking、确定时延配置 | DSP/量化推理 |
| 9 | 平台 gotchas | W1C 寄存器、电压容差、各平台坑点 | 移植排错 |

## 使用方式

这个 skill 是**知识库型提示词**——在需要写/改/调试 MCU 固件时，把它作为专家上下文喂给 AI。典型触发：

- "帮我写一个 STM32 的 SPI 传感器驱动（非阻塞 + DMA）"
- "这段代码加了 print 就正常，去掉就崩，帮我分析"
- "DMA 收数偶发数据错乱，是不是缓存一致性问题"
- "Hardfault 了，帮我定位是栈溢出还是越界"

## 为什么对你特别值

你的 TFLM 部署实践（跑 STM32/nRF）会密集踩到它覆盖的坑——尤其是 **DMA 缓冲区 32 字节对齐**（缓存行大小）和 **M7 弱序内存**导致的"加 print 正常、去掉就崩"。这正是嵌入式岗面试和技术深度最容易被问到的点，和你 `tech-interview-notes` 里的 Tickless/PendSV/启动流程互相印证。

## 关键要点（Gotchas）⭐

- **M7 弱序内存**：寄存器读写会被重排，必须用 `__DMB()`/`__DSB()` 包一层 mmio 访问，否则出现"加了 print 就正常"的经典症状。
- **DMA 缓冲区必须 32 字节对齐**，且大小是 32 的倍数，否则 cache invalidate 会破坏相邻内存。
- **W1C 寄存器**（USBSTS 等）是写 1 清零，`status &= ~bit` 是错的、无效的。
- **临界区保持微秒级**，优先 BASEPRI 而非 PRIMASK（保留高优先级中断响应能力）。
- **Rust 禁用 `static mut`**（UB），用 `AtomicBool` / `Mutex<RefCell>` + critical_section。

## 参考

- 本体原文：[[SKILL]]
- 项目仓库：https://github.com/wshobson/agents
- 相关：[[../index|Skills 库总览]]、[[../../career-development/index|职业发展]]

---

**标签**：`#embedded` `#cortex-m` `#firmware` `#driver` `#dma` `#memory-safety`
