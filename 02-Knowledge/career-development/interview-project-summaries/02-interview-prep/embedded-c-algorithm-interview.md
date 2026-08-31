# 嵌入式C语言算法MS题精选

> 来源：已有MS资料 + 网络整理
> 适用岗位：嵌入式软件工程师 / C语言开发
> 整理日期：2026-06-12

---

## 一、数据结构类

### 1. 环形队列（Ring Buffer / Circular Queue）

嵌入式最常用的数据结构，UART/DMA/音频缓冲必备。

```c
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint8_t *buffer;
    uint32_t size;
    volatile uint32_t read;   // 读指针
    volatile uint32_t write;  // 写指针
} ring_buffer_t;

// 初始化
void rb_init(ring_buffer_t *rb, uint8_t *buf, uint32_t size) {
    rb->buffer = buf;
    rb->size = size;
    rb->read = 0;
    rb->write = 0;
}

// 判断空：读指针 == 写指针
bool rb_is_empty(ring_buffer_t *rb) {
    return rb->read == rb->write;
}

// 判断满：(write + 1) % size == read（保留一个空位）
bool rb_is_full(ring_buffer_t *rb) {
    return ((rb->write + 1) % rb->size) == rb->read;
}

// 入队：写入一个字节
bool rb_put(ring_buffer_t *rb, uint8_t data) {
    if (rb_is_full(rb))
        return false;
    rb->buffer[rb->write] = data;
    rb->write = (rb->write + 1) % rb->size;
    return true;
}

// 出队：读取一个字节
bool rb_get(ring_buffer_t *rb, uint8_t *data) {
    if (rb_is_empty(rb))
        return false;
    *data = rb->buffer[rb->read];
    rb->read = (rb->read + 1) % rb->size;
    return true;
}

// 获取当前元素个数
uint32_t rb_count(ring_buffer_t *rb) {
    return (rb->write - rb->read + rb->size) % rb->size;
}
```

**MS追问**：为什么用 `volatile`？为什么保留一个空位？读写指针同时被中断和主循环访问怎么办？

> `volatile` 防止编译器优化；保留一个空位区分空/满状态；对于单生产者单消费者场景，原子操作即可；多生产者需要关中断或加锁。

## volatile 的本质：编译器优化禁令，和硬件无关
volatile 是 C 语言的关键字，作用对象是**编译器**，不是硬件。它只做三件事：
1. **禁止寄存器缓存**：不许把变量暂存到 CPU 通用寄存器里，每次读写都必须走内存总线；
2. **禁止读写重排**：不许把 volatile 变量的读写指令和其他指令乱序重排；
3. **禁止冗余读写删除**：不许把看似重复的读写操作优化掉，哪怕上一行刚读过，下一行也要重新读。

它不改变硬件行为，也不操作硬件寄存器，只是强制编译器生成「老老实实访问内存地址」的汇编指令，不做投机优化。

**三追问完整解答（答题卡，2026-08-31 补充）**：

1. **为什么 volatile**：编译器不知道 `read`/`write` 会被中断修改，不加 volatile 会把循环里反复读的值缓存进寄存器，导致主循环永远看不到中断的更新。volatile 强制每次从内存重读。
   - ⚠️ 三误解：`volatile` ≠ **原子性**（64 位变量在 32 位 MCU 上仍可能拆两次读）、≠ **线程安全**（不提供互斥）、≠ **内存屏障**（不保证指令顺序和 Cache 一致性）。

2. **为什么留一个空位**：区分「空」和「满」。不留空位则 `read==write` 同时表示空和满，无法区分。

   | 方案    | 空判断       | 满判断                | 代价                          |
   |:--------|:-------------|:----------------------|:------------------------------|
   | 留空位  | `read==write` | `(write+1)%size==read` | 容量 = size - 1               |
   | count计数 | `count==0`  | `count==size`         | 容量不浪费，但 count 需原子操作 |

3. **读写指针并发**：SPSC（中断写 / 主循环读）**天然无锁**——写方只改 `write`、读方只改 `read`，互不干扰。前提：`read`/`write` 独立，且读写原子（`uint32_t` 在 32 位 MCU 上单次读写原子）。**多生产者**才需关中断（临界区）或加锁。

> **一句话脱口版**：「volatile 是防编译器优化，强制每次从内存读，但不等于原子性/线程安全/内存屏障；留空位是为了区分空满——否则 read==write 空满不分，替代方案是 count 但要多生产者保护；SPSC 场景下读写指针分离、天然无锁，前提是指针独立且读写原子，只有多生产者才关中断保护。」

> **读写原子：如果指针是 uint64_t（在 32 位 MCU 上），读它要两条指令：读低 32 位 + 读高 32 位。中间被中断打断，就会读到「低 32 位是新值、高 32 位是旧值」的撕裂值——满空判断直接错乱。
---

### 2. 栈实现（数组版）

```c
typedef struct {
    int *data;
    int top;
    int capacity;
} stack_t;

void stack_init(stack_t *s, int *buf, int cap) {
    s->data = buf;
    s->top = -1;
    s->capacity = cap;
}

bool stack_push(stack_t *s, int val) {
    if (s->top + 1 >= s->capacity) return false;
    s->data[++(s->top)] = val;
    return true;
}

bool stack_pop(stack_t *s, int *val) {
    if (s->top < 0) return false;
    *val = s->data[(s->top)--];
    return true;
}
```

---

### 3. 链表反转（单向链表）

```c
typedef struct node {
    int data;
    struct node *next;
} node_t;

// 迭代法反转
node_t *reverse_list(node_t *head) {
    node_t *prev = NULL, *curr = head, *next = NULL;
    while (curr != NULL) {
        next = curr->next;      // 保存后继
        curr->next = prev;      // 反转指向
        prev = curr;            // prev前进
        curr = next;            // curr前进
    }
    return prev;                // 新头节点
}

// 递归法反转
node_t *reverse_list_recursive(node_t *head) {
    if (head == NULL || head->next == NULL)
        return head;
    node_t *new_head = reverse_list_recursive(head->next);
    head->next->next = head;
    head->next = NULL;
    return new_head;
}
```

---

### 4. 括号匹配（栈应用）

```c
#include <stdbool.h>
#include <string.h>

bool isValid(char *s) {
    int len = strlen(s);
    if (len % 2 != 0) return false;  // 奇数长度一定无效

    char stack[len];
    int top = -1;

    for (int i = 0; i < len; i++) {
        char c = s[i];
        if (c == '(' || c == '[' || c == '{') {
            stack[++top] = c;                     // 左括号入栈
        } else {
            if (top == -1) return false;           // 栈空→无匹配左括号
            char left = stack[top--];
            if ((c == ')' && left != '(') ||
                (c == ']' && left != '[') ||
                (c == '}' && left != '{'))
                return false;                      // 类型不匹配
        }
    }
    return top == -1;  // 最后栈空才有效
}
```

---

## 二、字符串/内存操作类

### 5. strlen 实现

```c
size_t my_strlen(const char *str) {
    const char *p = str;
    while (*p != '\0') p++;
    return p - str;
}

// MS追问：不用临时变量？递归版？
size_t my_strlen2(const char *str) {
    if (*str == '\0') return 0;
    return 1 + my_strlen2(str + 1);
}
```

### 6. strcpy 实现

```c
char *my_strcpy(char *dest, const char *src) {
    char *ret = dest;
    while ((*dest++ = *src++) != '\0');
    return ret;  // 返回 dest 首地址，支持链式调用
}
// MS加分：考虑内存重叠？改用 memmove
```

### 7. memcpy 实现（按字节拷贝）

```c
void *my_memcpy(void *dest, const void *src, size_t n) {
    char *d = (char *)dest;
    const char *s = (const char *)src;
    for (size_t i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

// 优化版：按4字节对齐拷贝（MS亮了！）
void *my_memcpy_fast(void *dest, const void *src, size_t n) {
    char *d = (char *)dest;
    const char *s = (const char *)src;
    // 先处理不对齐的头尾，中间用 uint32_t 批量拷贝
    while (n >= 4 && ((uintptr_t)d & 3) == 0 && ((uintptr_t)s & 3) == 0) {
        *(uint32_t *)d = *(uint32_t *)s;
        d += 4; s += 4; n -= 4;
    }
    // 剩余部分逐字节拷贝
    while (n--) *d++ = *s++;
    return dest;
}
```

**MS追问**：memcpy 和 memmove 的区别？

> memcpy 不保证重叠内存安全；memmove 会先判断 dest 和 src 相对位置，选择正向或反向拷贝，保证重叠内存正确。

### 8. strcmp 实现

```c
int my_strcmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++; s2++;
    }
    return *(unsigned char *)s1 - *(unsigned char *)s2;
}
```

---

## 三、排序与查找类

### 9. 冒泡排序

```c
void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int swapped = 0;
        for (int j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                int tmp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = tmp;
                swapped = 1;
            }
        }
        if (!swapped) break;  // 已有序，提前退出
    }
}
```

### 10. 快速排序

```c
void quick_sort(int arr[], int low, int high) {
    if (low >= high) return;

    int pivot = arr[low];      // 选第一个为基准
    int i = low, j = high;

    while (i < j) {
        while (i < j && arr[j] >= pivot) j--;
        if (i < j) arr[i++] = arr[j];

        while (i < j && arr[i] <= pivot) i++;
        if (i < j) arr[j--] = arr[i];
    }
    arr[i] = pivot;

    quick_sort(arr, low, i - 1);
    quick_sort(arr, i + 1, high);
}
```

### 11. 二分查找

```c
int binary_search(int arr[], int size, int target) {
    int left = 0, right = size - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;  // 防溢出写法
        if (arr[mid] == target)
            return mid;
        else if (arr[mid] < target)
            left = mid + 1;
        else
            right = mid - 1;
    }
    return -1;  // 未找到
}
```

---

## 四、位操作与底层类

### 12. 大小端判断

```c
// 方法1：联合体法
int is_little_endian(void) {
    union {
        int i;
        char c;
    } u = {1};
    return u.c == 1;  // 1=小端，0=大端
}

// 方法2：指针法
int is_little_endian2(void) {
    int n = 1;
    return *(char *)&n == 1;
}
```

### 13. 位操作常用宏

```c
#define SET_BIT(reg, n)    ((reg) |=  (1 << (n)))    // 置位
#define CLR_BIT(reg, n)    ((reg) &= ~(1 << (n)))    // 清零
#define GET_BIT(reg, n)    ((reg) &   (1 << (n)))    // 读取
#define TOGGLE_BIT(reg, n) ((reg) ^=  (1 << (n)))    // 翻转

// 嵌入式常用：寄存器位域操作
#define READ_REG(addr)      (*(volatile uint32_t *)(addr))
#define WRITE_REG(addr, val) (*(volatile uint32_t *)(addr) = (val))
```

### 14. 不用临时变量交换两个数

```c
// 方法1：异或法（经典）
void swap_xor(int *a, int *b) {
    *a = *a ^ *b;
    *b = *a ^ *b;
    *a = *a ^ *b;
}

// 方法2：加减法（可能溢出）
void swap_add(int *a, int *b) {
    *a = *a + *b;
    *b = *a - *b;
    *a = *a - *b;
}

// MS追问：异或法的限制？
// → a和b不能指向同一地址（自己异或自己=0）
```

---

## 五、综合题

### 15. 斐波那契数列

```c
// 迭代版（MS首选，O(n)时间 O(1)空间）
int fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}

// 递归版（简洁但 O(2^n)，MS官可能追问缺点）
int fib_recursive(int n) {
    if (n <= 1) return n;
    return fib_recursive(n - 1) + fib_recursive(n - 2);
}
```

### 16. 判断回文字符串

```c
#include <stdbool.h>
#include <string.h>

bool is_palindrome(const char *s) {
    int left = 0, right = strlen(s) - 1;
    while (left < right) {
        if (s[left] != s[right])
            return false;
        left++; right--;
    }
    return true;
}
```

### 17. 字符串翻转

```c
void reverse_string(char *s) {
    int len = strlen(s);
    for (int i = 0; i < len / 2; i++) {
        char tmp = s[i];
        s[i] = s[len - 1 - i];
        s[len - 1 - i] = tmp;
    }
}
```

---

## 六、MS高频考点速查

| 考点 | 关键词 | MS概率 |
|------|------|:--:|
| 环形队列 | FIFO、volatile、无锁实现 | ⭐⭐⭐⭐⭐ |
| 链表反转 | 迭代/递归、内存安全 | ⭐⭐⭐⭐ |
| memcpy/strcpy 实现 | 重叠内存、对齐优化 | ⭐⭐⭐⭐⭐ |
| 大小端判断 | 联合体、网络序 | ⭐⭐⭐⭐ |
| 位操作 | SET/CLEAR/GET/TOGGLE | ⭐⭐⭐⭐⭐ |
| 快排/二分查找 | 分治、边界条件 | ⭐⭐⭐ |
| 括号匹配 | 栈应用 | ⭐⭐⭐ |
| 字符串翻转/回文 | 双指针 | ⭐⭐ |

---

> **回答策略**：先写基础实现，再说优化点（如 memcpy 4字节对齐），最后提边界条件（如重叠内存、空指针）。MS官要看的不是你写的代码多快，而是你能考虑到多少边界情况。
