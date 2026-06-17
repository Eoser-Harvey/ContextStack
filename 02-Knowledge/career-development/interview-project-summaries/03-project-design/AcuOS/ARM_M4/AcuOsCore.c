/**************************************************************************
* 文件名称：AcuOsCore.c
* 文件说明：AcuOsCore
* 版 本：   V1.01
* 作 者：   吴志亮
* 日 期：   2018-08-01
*
**************************************************************************/

#include "AcuOs.h"


static Uint32 g_uiOsIdleCnt = 0;
static Uint32 g_uiOsIdleCntMax = 0;

Uint32 g_uiOsCpuUsage = 0;

T_OsTcb *g_ptCurrentTcb = NULL;
T_OsTcb *g_ptReadyTcb   = NULL;


static T_OsTcb g_atOsTaskTcbTable[OS_MAX_TASKS];
static Uint32 g_uiOsTaskCount = 0;
static Uint32 g_uiOsTaskCountBakup = 0;

static Uint32 g_auiTaskIdleStk[OS_TASK_STK_SIZE];
static Uint32 g_auiTaskStatStk[OS_TASK_STK_SIZE];

static void OsTaskIdle(void);
static void OsTaskStatus(void);


static void OsContextSwitchInt(void)
{
    NVIC_INT_CTRL = NVIC_PENDSV_SET;
}

static void OsPreSchedule(void)
{
    T_OsTcb *ptTcb;
    Uint32 i;
    
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
 
    for (i = 0; i < g_uiOsTaskCount; i++)
    {
        ptTcb = (T_OsTcb*)&g_atOsTaskTcbTable[i];
        
        if (OS_EVENT_STATUS_READY == ptTcb->ptEvent->uiStatus)
        {
            if (OS_TASK_STAT_PEND_EVENT == ptTcb->uiStatus)
            {
                ptTcb->uiStatus = OS_TASK_STAT_READY;
            }
        }
    }
    OS_EXIT_CRITICAL();
}


static void OsSchedule(void)
{
    T_OsTcb *ptTcb;
    Uint32 i;
    
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    /* task status switch */
    OsPreSchedule();
    
    /* get ready tcb */
    g_ptReadyTcb = (T_OsTcb*)&g_atOsTaskTcbTable[0];
    
    for (i = 0; i < g_uiOsTaskCount; i++)
    {
        ptTcb = (T_OsTcb*)&g_atOsTaskTcbTable[i];
        
        if (OS_TASK_STAT_READY == ptTcb->uiStatus)
        {
            if (g_ptReadyTcb->uiPriority > ptTcb->uiPriority)
            {
                g_ptReadyTcb = ptTcb;
            }
        }
    }
    
    /* task switch */    
    OsContextSwitchInt();                // 开启PendSV中断，进行任务切换
    
    OS_EXIT_CRITICAL();
}

void OsTimeTick(void)
{
    T_OsTcb *ptTcb;
    Uint32 i;
    
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    for (i = 0; i < g_uiOsTaskCount; i++)
    {
        ptTcb = (T_OsTcb*)&g_atOsTaskTcbTable[i];
        
        if (ptTcb->uiTimeDly == 0)
        {
            if (OS_TASK_STAT_PEND_DLY == ptTcb->uiStatus)
            {
                ptTcb->uiStatus = OS_TASK_STAT_READY;
            }
            else if (OS_TASK_STAT_PEND_EVENT == ptTcb->uiStatus)
            {
                if (OS_EVENT_OPT_NONE_BLOCK == ptTcb->ptEvent->uiBlockOpt)
                {
                    ptTcb->uiStatus = OS_TASK_STAT_READY;
                }
            }
        }
        else
        {
            ptTcb->uiTimeDly--;
        }
    }
    
    OS_EXIT_CRITICAL();
    
    OsSchedule();
}

static void OsTimeDly(Uint32 uiTick)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    g_ptCurrentTcb->uiTimeDly = uiTick;
    g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_DLY;
    
    OS_EXIT_CRITICAL();
    
    OsSchedule();
}
void OsTimeDlyMs(Uint32 uiMs)
{
    OsTimeDly(uiMs * OS_PER_SECOND_TICKS / 1000);
}

void OsIntEnter(void)
{

}

void OsIntExit(void)
{
    OsSchedule();
}


static Uint32 *OsTaskStkInit (void (*pTask)(void), Uint32 *puiTos)
{
    Uint32 *puiStk;

    puiStk      = puiTos;                       /* Load top of stack pointer */

    /* Registers stacked as if auto-saved on exception      */
    /* xPSR <-- EntryPoint(PC) <-- R14(LR) <-- R12 <-- R3 <-- R2 <-- R1 <-- R0(Argument)*/
    
    *(puiStk)   = (Uint32)0x01000000u;                      
    *(--puiStk) = (Uint32)pTask;                            
    *(--puiStk) = (Uint32)pTask;                            
    *(--puiStk) = (Uint32)0x12121212u;                      
    *(--puiStk) = (Uint32)0x03030303u;                      
    *(--puiStk) = (Uint32)0x02020202u;                      
    *(--puiStk) = (Uint32)0x01010101u;                      
    *(--puiStk) = (Uint32)0x00000000u;                      
        
    /* Remaining registers saved on process stack            */
    /* R11 <-- R10 <-- R9 <-- R8 <-- R7 <-- R6 <-- R5 <-- R4 */
    
    *(--puiStk) = (Uint32)0x11111111u;
    *(--puiStk) = (Uint32)0x10101010u;
    *(--puiStk) = (Uint32)0x09090909u;
    *(--puiStk) = (Uint32)0x08080808u;
    *(--puiStk) = (Uint32)0x07070707u;
    *(--puiStk) = (Uint32)0x06060606u;
    *(--puiStk) = (Uint32)0x05050505u;
    *(--puiStk) = (Uint32)0x04040404u;
    
    return (puiStk);
}

Uint8 OsTaskCreate(void (*pTask)(void), Uint32 *puiTos, Uint32 uiPrio)
{
    T_OsTcb *ptTcb;
    
    if (uiPrio > OS_MAX_TASKS)
    {
        return 1;
    }
    
    if (g_uiOsTaskCount > (OS_MAX_TASKS - 1))
    {
        return 2;
    }
    
    ptTcb = (T_OsTcb*)&g_atOsTaskTcbTable[g_uiOsTaskCount];
    g_uiOsTaskCount++;
    
    ptTcb->puiStk = OsTaskStkInit(pTask, puiTos);
    ptTcb->uiTimeDly = 0;
    ptTcb->uiPriority = uiPrio;
    ptTcb->uiStatus = OS_TASK_STAT_READY;
    ptTcb->ptEvent = NULL;
    
    return 0;
}

void OsTaskInit(void)
{
    g_uiOsTaskCount = 0;
    
    OsTaskCreate(OsTaskIdle, &g_auiTaskIdleStk[OS_TASK_STK_SIZE - 1],OS_MAX_TASKS);
    OsTaskCreate(OsTaskStatus, &g_auiTaskStatStk[OS_TASK_STK_SIZE - 1],(OS_MAX_TASKS - 1));
    
    g_ptCurrentTcb = (T_OsTcb*)&g_atOsTaskTcbTable[0];
    g_ptReadyTcb = (T_OsTcb*)&g_atOsTaskTcbTable[0];
}

static void OsTaskStatusInit(void)
{
    g_uiOsIdleCntMax = 0;
    g_uiOsTaskCountBakup = g_uiOsTaskCount;
    g_uiOsTaskCount = 2;                        /* Task Idle and Status */
}

void OsTaskStart(void)
{
    OsTaskStatusInit();
    
    OsStartFirstTask();
}


static void OsTaskIdle(void)
{
    OS_ALLOC_CRITICAL();
    
    while(1)
    {
        OS_ENTER_CRITICAL();
        g_uiOsIdleCnt++;
        OS_EXIT_CRITICAL();
    }
}

static void OsTaskStatus(void)
{
    Uint32 uiOsIdleCntRun = 0;
    
    OS_ALLOC_CRITICAL();
    
    while(1)
    {        
        if (0 != g_uiOsIdleCntMax)
        {
            OS_ENTER_CRITICAL();
            uiOsIdleCntRun = g_uiOsIdleCnt;
            g_uiOsIdleCnt = 0;
            OS_EXIT_CRITICAL();
            
            /* CpuUsage percent % */
            g_uiOsCpuUsage = 100 - (100 * uiOsIdleCntRun / g_uiOsIdleCntMax);   
            
            OsTimeDly(OS_PER_SECOND_TICKS);       
        }
        else
        {
            OS_ENTER_CRITICAL();
            g_uiOsIdleCnt = 0;
            OS_EXIT_CRITICAL();
            
            OsTimeDly(OS_PER_SECOND_TICKS);
            
            OS_ENTER_CRITICAL();
            g_uiOsIdleCntMax = g_uiOsIdleCnt;
            g_uiOsIdleCnt = 0;
            g_uiOsTaskCount = g_uiOsTaskCountBakup;
            OS_EXIT_CRITICAL();            
        }
    }
}


/* Sem Create Post Pend */

void OsSemCreate(T_OsSem *ptSem, Uint32 uiCntVal, Uint32 uiBlockOpt)
{
    ptSem->uiCnt = uiCntVal;
    
    ptSem->tEvent.uiType = OS_EVENT_TYPE_SEM;
    ptSem->tEvent.uiBlockOpt = uiBlockOpt;
    
    if (ptSem->uiCnt > 0)
    {
        ptSem->tEvent.uiStatus = OS_EVENT_STATUS_READY;
    }
    else
    {
        ptSem->tEvent.uiStatus = OS_EVENT_STATUS_PEND;
    }
}

void OsSemPost(T_OsSem *ptSem)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    if (OS_EVENT_STATUS_PEND == ptSem->tEvent.uiStatus)
    {
        ptSem->tEvent.uiStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return ;
    }
    
    ptSem->uiCnt++;
    OS_EXIT_CRITICAL();
}

void OsSemPend(T_OsSem *ptSem, Uint32 uiTimeOut)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    if (ptSem->uiCnt > 0)
    {
        ptSem->uiCnt--;
        OS_EXIT_CRITICAL();
        return ;
    }
    
    ptSem->tEvent.uiStatus = OS_EVENT_STATUS_PEND;

    g_ptCurrentTcb->uiTimeDly = uiTimeOut;
    g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptSem->tEvent);
    g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
    OS_EXIT_CRITICAL();
            
    OsSchedule();
}





/* Q Create Post Pend */

void OsQCreate(T_OsQ *ptQ, Uint32 uiLength, Uint32 uiBlockOpt)
{
    if (uiLength > OS_MAX_Q_SIZE)
    {
        return ;
    }
    
    ptQ->uiLength = uiLength;
    ptQ->uiCount = 0;
    ptQ->puiHead = (Uint32 *)&(ptQ->pauiBufQ[0]);
    ptQ->puiTail = (Uint32 *)&(ptQ->pauiBufQ[0]);
    
    
    ptQ->tEvent.uiType = OS_EVENT_TYPE_Q;
    ptQ->tEvent.uiBlockOpt = uiBlockOpt;
    ptQ->tEvent.uiStatus = OS_EVENT_STATUS_PEND;
}

void OsQPost(T_OsQ *ptQ, void *pMsg)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    if (ptQ->uiCount == OS_MAX_Q_SIZE)
    {
        OS_EXIT_CRITICAL();
        return ;
    }
    
    *(ptQ->puiHead) = (Uint32)pMsg;
    ptQ->uiCount++;
    
    if (ptQ->puiHead == (Uint32 *)&(ptQ->pauiBufQ[OS_MAX_Q_SIZE - 1]))
    {
        ptQ->puiHead = (Uint32 *)&(ptQ->pauiBufQ[0]);
    }
    else
    {
        ptQ->puiHead++;
    }
    
    if (OS_EVENT_STATUS_PEND == ptQ->tEvent.uiStatus)
    {
        ptQ->tEvent.uiStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return ;
    }
    
    OS_EXIT_CRITICAL();
}

void *OsQPend(T_OsQ *ptQ, Uint32 uiTimeOut)
{
    void *pMsg = NULL;
    
    OS_ALLOC_CRITICAL();
    
    if (ptQ->uiCount == 0)
    {
        OS_ENTER_CRITICAL();
        ptQ->tEvent.uiStatus = OS_EVENT_STATUS_PEND;

        g_ptCurrentTcb->uiTimeDly = uiTimeOut;
        g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptQ->tEvent);
        g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
        OS_EXIT_CRITICAL();
                
        OsSchedule();
    }
    
    OS_ENTER_CRITICAL();
    if (ptQ->uiCount > 0)
    {
        pMsg = (void *)*(ptQ->puiTail);
        ptQ->uiCount--;
        
        if (ptQ->puiTail == (Uint32 *)&(ptQ->pauiBufQ[OS_MAX_Q_SIZE - 1]))
        {
            ptQ->puiTail = (Uint32 *)&(ptQ->pauiBufQ[0]);
        }
        else
        {
            ptQ->puiTail++;
        }
    }
    else
    {
        OS_EXIT_CRITICAL();
        return NULL;
    }
       
    OS_EXIT_CRITICAL();
    return (pMsg);
}




