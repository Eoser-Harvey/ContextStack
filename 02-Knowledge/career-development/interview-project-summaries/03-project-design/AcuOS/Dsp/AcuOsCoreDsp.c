/**************************************************************************
* 文件名称：AcuOsCore.c
* 文件说明：AcuOsCore
* 版 本：   V1.01
* 作 者：   hanwei
* 日 期：   2021-01-11
*
**************************************************************************/

#include "AcuOs.h"

/**************************************************************************/

#define OS_TASK_STK_SIZE                200

#define OS_TASK_STAT_READY              1
#define OS_TASK_STAT_PEND_DLY           2
#define OS_TASK_STAT_PEND_EVENT         3


#define OS_EVENT_TYPE_SEM               1
#define OS_EVENT_TYPE_Q                 2
#define OS_EVENT_TYPE_FLAG              3
#define OS_EVENT_TYPE_MUTEX             4

#define OS_EVENT_STATUS_PEND            1
#define OS_EVENT_STATUS_READY           2




/**************************************************************************/

static Uint32 g_uiOsIdleCnt = 0;
static Uint32 g_uiOsIdleCntMax = 0;
static Uint32 g_uiOsCpuUsage = 0;

T_OsTcb *g_ptCurrentTcb = NULL;
T_OsTcb *g_ptReadyTcb   = NULL;


static T_OsTcb *g_ptOsTaskTcbTableHead = NULL;

static Uint32 g_uiOsTimeTickCount = 0;

static Uint32 g_uiOsTimeTickMsCnt = 0;
static Uint32 g_uiOsTimeTickSecCnt = 0;
static Uint32 g_uiOsRunTimeSec = 0;

static T_OsTimer *g_ptOsTimerHead = NULL;


static Uint32 g_auiTaskIdleStk[OS_TASK_STK_SIZE] = {0};
static Uint32 g_auiTaskStatStk[OS_TASK_STK_SIZE] = {0};
static Uint32 g_auiTaskTimerStk[OS_TASK_STK_SIZE] = {0};

static T_OsTcb g_tOsTcbTaskIdle;
static T_OsTcb g_tOsTcbTaskStatus;
static T_OsTcb g_tOsTcbTaskTimer;

/**************************************************************************/

static void OsTaskIdle(void);
static void OsTaskStatus(void);
static void OsTaskTimer(void);

/**************************************************************************/

static inline void OsPreSchedule(void)
{
    T_OsTcb *ptTcb = NULL;
    
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    ptTcb = g_ptOsTaskTcbTableHead;
    while (NULL != ptTcb)
    {
        if (OS_EVENT_STATUS_READY == ptTcb->ptEvent->ucStatus)
        {
            if (OS_TASK_STAT_PEND_EVENT == ptTcb->uiStatus)
            {
                ptTcb->uiStatus = OS_TASK_STAT_READY;
            }
        }
        
        ptTcb = ptTcb->ptNext;
    }
    
    OS_EXIT_CRITICAL();
}


static void OsSchedule(void)
{
    T_OsTcb *ptTcb = NULL;
    
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    /* task status switch */
    OsPreSchedule();
    
    /* get ready tcb */
    g_ptReadyTcb = g_ptOsTaskTcbTableHead;
    
    ptTcb = g_ptOsTaskTcbTableHead;
    while (NULL != ptTcb)
    {
        if (OS_TASK_STAT_READY == ptTcb->uiStatus)
        {
            if (g_ptReadyTcb->uiPriority > ptTcb->uiPriority)
            {
                g_ptReadyTcb = ptTcb;
            }
        }
        
        ptTcb = ptTcb->ptNext;
    }
    
    /* task switch */ 
    if (g_ptReadyTcb != g_ptCurrentTcb)
    {   
        OsContextSwitchInt();    
    }
    
    OS_EXIT_CRITICAL();
}

static inline void OsTickDlyCheck(void)
{
	T_OsTcb *ptTcb = NULL;
    
    ptTcb = g_ptOsTaskTcbTableHead;
    while (NULL != ptTcb)
    {
        if (ptTcb->uiTimeDly == 0)
        {
            if (OS_TASK_STAT_PEND_DLY == ptTcb->uiStatus)
            {
                ptTcb->uiStatus = OS_TASK_STAT_READY;
            }
            else if (OS_TASK_STAT_PEND_EVENT == ptTcb->uiStatus)
            {
                if (OS_EVENT_OPT_NONE_BLOCK == ptTcb->ptEvent->ucBlockOpt)
                {
                    ptTcb->uiStatus = OS_TASK_STAT_READY;
                }
            }
        }
        else
        {
            ptTcb->uiTimeDly--;
        }
        
        ptTcb = ptTcb->ptNext;
    }
}

static inline void OsTimeMsSecCnt(void)
{
    g_uiOsTimeTickMsCnt++;
    
    if (g_uiOsTimeTickMsCnt >= OS_PER_SECOND_TICKS)
    {
        g_uiOsTimeTickMsCnt = 0;
        g_uiOsTimeTickSecCnt++;
		g_uiOsRunTimeSec++;
    }
}

void OsTimeTick(void)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    g_uiOsTimeTickCount++;
    
    OsTimeMsSecCnt();
    
    OsTickDlyCheck();
    
    OsSchedule();
    
    OS_EXIT_CRITICAL();
}

static inline void OsTimeDly(Uint32 uiTick)
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

static Uint8 inline OsTaskTotalCount(T_OsTcb *ptTcb)
{
    Uint8 ucCount = 0;
    
    T_OsTcb *ptT = ptTcb;
    
    while (NULL != ptT)
    {
        ucCount++;
        ptT = ptT->ptNext;
    }
    
    return ucCount;
}

static void OsTaskStkCheck(T_OsTcb *ptTcb)
{
    Uint32 *puiStkChk = NULL;
    Uint32 uiFree = 0;
    
    T_OsTcb *ptT = ptTcb;
    
    while (NULL != ptT)
    {
        puiStkChk = ptT->puiStkBot;
        
        uiFree = 0;
        while ((0 == *puiStkChk++) && (uiFree < ptT->uiStkFree))
        {
            uiFree++;
        }
        ptT->uiStkFree = uiFree;
        
        ptT = ptT->ptNext;
    }
}

Uint8 OsTaskCreate(void (*pTask)(void), T_OsTcb *ptOsTcb, Uint32 *puiStk, Uint32 uiStkSize, Uint32 uiPrio)
{
    T_OsTcb *ptTcb = NULL;
    
    if (OsTaskTotalCount(g_ptOsTaskTcbTableHead) > OS_MAX_TASKS)
    {
        return OS_ERROR_TASK_MAX;
    }
    
    if (uiPrio > OS_MAX_TASKS)
    {
        return OS_ERROR_TASK_PRIO;
    }
    
    if (NULL == g_ptOsTaskTcbTableHead)
    {
        g_ptOsTaskTcbTableHead = ptOsTcb;
		ptOsTcb->ptNext = NULL;
    }
	else
	{
		ptTcb = g_ptOsTaskTcbTableHead;
		while (NULL != ptTcb->ptNext)
		{
			ptTcb = ptTcb->ptNext;
		}
		ptTcb->ptNext = ptOsTcb;
		ptOsTcb->ptNext = NULL;
	}
    
    ptOsTcb->puiStkTop = OsTaskStkInit(pTask, puiStk, uiStkSize);
    ptOsTcb->puiStkBot = puiStk;
    ptOsTcb->uiStkFree = uiStkSize;
    ptOsTcb->uiTimeDly = 0;
    ptOsTcb->uiPriority = uiPrio;
    ptOsTcb->uiStatus = OS_TASK_STAT_READY;
    ptOsTcb->ptEvent = NULL;
    
    return OS_ERROR_NONE;
}

void OsTaskInit(void)
{
    OsTaskCreate(OsTaskIdle, &g_tOsTcbTaskIdle, g_auiTaskIdleStk, OS_TASK_STK_SIZE, OS_MAX_TASKS);
    OsTaskCreate(OsTaskStatus, &g_tOsTcbTaskStatus, g_auiTaskStatStk, OS_TASK_STK_SIZE, (OS_MAX_TASKS - 1));
    OsTaskCreate(OsTaskTimer, &g_tOsTcbTaskTimer, g_auiTaskTimerStk, OS_TASK_STK_SIZE, (OS_MAX_TASKS - 2));
    
    g_ptCurrentTcb = g_ptOsTaskTcbTableHead;
    g_ptReadyTcb = g_ptOsTaskTcbTableHead;
}

static void OsTaskStatusInit(void)
{
    g_uiOsIdleCntMax = 0;
    
    g_ptCurrentTcb = g_ptOsTaskTcbTableHead;
    g_ptReadyTcb = g_ptOsTaskTcbTableHead;
    
    /* Task Idle and Status , wait for icpu usage dle count */
    g_tOsTcbTaskStatus.ptNext = NULL;
}

void OsTaskStart(void)
{
    OsTaskStatusInit();
    
    OsStartFirstTask();
}

static void OsTaskIdle(void)
{
    OS_ALLOC_CRITICAL();
    
    while (1)
    {
        OS_ENTER_CRITICAL();
        g_uiOsIdleCnt++;
        OS_EXIT_CRITICAL();
    }
}

static void OsTaskStatus(void)
{    
    OS_ALLOC_CRITICAL();
    
    while (1)
    {        
        if (0 != g_uiOsIdleCntMax)
        {
            OS_ENTER_CRITICAL();
            
            /* CpuUsage percent % */
            g_uiOsCpuUsage = 100 - (100 * g_uiOsIdleCnt / g_uiOsIdleCntMax);
            g_uiOsIdleCnt = 0;  
            
            OS_EXIT_CRITICAL();
            
            /* Check Stack Free Size */
            OsTaskStkCheck(g_ptOsTaskTcbTableHead);
            
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
            g_tOsTcbTaskStatus.ptNext = &g_tOsTcbTaskTimer;
            OS_EXIT_CRITICAL();
            
            OsTimeDly(OS_PER_SECOND_TICKS);
        }
    }
}

static inline void OsTaskTimerUpProc(T_OsTimer *ptTmr)
{
    if (OS_TIMER_MODE_PERIOD == ptTmr->ucMode)
    {
        ptTmr->uiTimerDly = ptTmr->uiTimePeriod;
        if (NULL != ptTmr->pFunc)
        {
            ptTmr->pFunc(ptTmr->pArg);
        }
    }
    else if (OS_TIMER_MODE_ONCE == ptTmr->ucMode)
    {
        ptTmr->ucEnable = 0;
        ptTmr->uiTimerDly = 0;
        if (NULL != ptTmr->pFunc)
        {
            ptTmr->pFunc(ptTmr->pArg);
        }
    }
    else
    {
        ptTmr->ucEnable = 0;
    }
}

static Uint32 g_uiCurrentBakupTick = 0;

static void OsTaskTimerListProc(void)
{
  	Uint32 uiCurrentTick = 0;
    Uint32 uiEscapeTicks = 0;
    
	T_OsTimer *ptTmr = NULL;
	
    if (NULL != g_ptOsTimerHead)
    {
        ptTmr = g_ptOsTimerHead;
        
        uiCurrentTick = g_uiOsTimeTickCount;
        if (uiCurrentTick >= g_uiCurrentBakupTick)
        {
            uiEscapeTicks = uiCurrentTick - g_uiCurrentBakupTick;
        }
        else
        {
            uiEscapeTicks = 4294967295 - g_uiCurrentBakupTick + uiCurrentTick + 1;
        }
        g_uiCurrentBakupTick = g_uiOsTimeTickCount;
    
        while (NULL != ptTmr)
        {
            if (1 == ptTmr->ucEnable)
            {
                if (ptTmr->uiTimerDly > uiEscapeTicks)
                {
                    ptTmr->uiTimerDly = ptTmr->uiTimerDly - uiEscapeTicks;
                
                    if (ptTmr->uiTimerDly <= uiEscapeTicks)
                    {
                        OsTaskTimerUpProc(ptTmr);
                    }
                }
                else
                {
                    OsTaskTimerUpProc(ptTmr);
                }
            }
        
            ptTmr = ptTmr->ptNext;
        }
    }
}

static void OsTaskTimer(void)
{
    while (1)
    {
		OsTaskTimerListProc();
		
		OsTimeDly(OS_TIMER_TICKS); 
    }
}

static Uint8 OsTimerTotalCount(T_OsTimer *ptTimer)
{
    Uint8 ucCount = 0;
    
    T_OsTimer *ptT = ptTimer;
    
    while (NULL != ptT)
    {
        ucCount++;
        ptT = ptT->ptNext;
    }
    
    return ucCount;
}

static Uint8 OsTimerCheckExist(T_OsTimer *ptTimer)
{
    T_OsTimer *ptTmr = NULL;

    ptTmr = g_ptOsTimerHead;
    
    while (NULL != ptTmr)
    {
        if (ptTmr == ptTimer)
        {
            return 1;
        }
        
        ptTmr = ptTmr->ptNext;
    }
    
    return 0;
}

Uint8 OsTimerCreate(T_OsTimer *ptTimer, Uint32 uiTimeMs, Uint8 ucMode, pFuncCallBackPtr pFunc, void *pArg)
{
    T_OsTimer *ptTmr = NULL;
    
    if (OsTimerTotalCount(g_ptOsTimerHead) > OS_MAX_TIMERS)
    {
        return OS_ERROR_TIMER_MAX;
    }
    
    if (OsTimerCheckExist(ptTimer) != 0)
    {
        return 2;
    }
    
    if (NULL == g_ptOsTimerHead)
    {
        g_ptOsTimerHead = ptTimer;
		ptTimer->ptNext = NULL;
    }
	else
	{
		ptTmr = g_ptOsTimerHead;
		while (NULL != ptTmr->ptNext)
		{
			ptTmr = ptTmr->ptNext;
		}
		ptTmr->ptNext = ptTimer;
		ptTimer->ptNext = NULL;
	}
	
	ptTimer->ucEnable = 0;
	ptTimer->ucMode = ucMode;
	ptTimer->uiTimePeriod = uiTimeMs * OS_PER_SECOND_TICKS / 1000;	/* Ticks */
	ptTimer->uiTimerDly = 0;
	ptTimer->pFunc = pFunc;
    ptTimer->pArg = pArg;
    
    return OS_ERROR_NONE;
}
void OsTimerStart(T_OsTimer *ptTimer)
{
    ptTimer->uiTimerDly = ptTimer->uiTimePeriod;
	ptTimer->ucEnable = 1;
}
void OsTimerStop(T_OsTimer *ptTimer)
{
    ptTimer->uiTimerDly = 0;
	ptTimer->ucEnable = 0;
}



Uint32 OsGetCpuUsagePercent(void)
{
    return g_uiOsCpuUsage;
}

Uint32 OsGetTaskCount(void)
{
    return OsTaskTotalCount(g_ptOsTaskTcbTableHead);
}

Uint32 OsGetTimerCount(void)
{
    return OsTimerTotalCount(g_ptOsTimerHead);
}





/* Sem Create Post Pend */

void OsSemCreate(T_OsSem *ptSem, Uint32 uiCntVal, Uint8 ucBlockOpt)
{
    ptSem->uiCnt = uiCntVal;
    
    ptSem->tEvent.ucType = OS_EVENT_TYPE_SEM;
    ptSem->tEvent.ucBlockOpt = ucBlockOpt;
    
    if (ptSem->uiCnt > 0)
    {
        ptSem->tEvent.ucStatus = OS_EVENT_STATUS_READY;
    }
    else
    {
        ptSem->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
    }
}

void OsSemPost(T_OsSem *ptSem)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    ptSem->uiCnt++;
    
    if (OS_EVENT_STATUS_PEND == ptSem->tEvent.ucStatus)
    {
        ptSem->tEvent.ucStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return ;
    }
    
    OS_EXIT_CRITICAL();
}

Uint8 OsSemPend(T_OsSem *ptSem, Uint32 uiTimeOut)
{
    OS_ALLOC_CRITICAL();
    
    if (0 == ptSem->uiCnt)
    {
        OS_ENTER_CRITICAL();
        ptSem->tEvent.ucStatus = OS_EVENT_STATUS_PEND;

        g_ptCurrentTcb->uiTimeDly = uiTimeOut;
        g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptSem->tEvent);
        g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
        OS_EXIT_CRITICAL();
        
        OsSchedule();   /* os pend */
    }
    
    OS_ENTER_CRITICAL();
    if (ptSem->uiCnt > 0)
    {
        ptSem->uiCnt--;
    }
    else
    {
        OS_EXIT_CRITICAL();
        return OS_ERROR_SEM_TIMEOUT;
    }
    
    OS_EXIT_CRITICAL();
    
    return OS_ERROR_NONE;
}




/* Q Create Post Pend */

Uint8 OsQCreate(T_OsQ *ptQ, Uint32 *puiMsgBuf, Uint32 uiMsgBufLen, Uint8 ucBlockOpt)
{
    if (NULL == puiMsgBuf)
    {
        return OS_ERROR_Q_BUF_NULL;
    }
    
    ptQ->puiBufQ = puiMsgBuf;
    
    ptQ->uiLength = uiMsgBufLen;
    ptQ->uiCount = 0;
    ptQ->puiHead = ptQ->puiBufQ;
    ptQ->puiTail = ptQ->puiBufQ;
    
    ptQ->tEvent.ucType = OS_EVENT_TYPE_Q;
    ptQ->tEvent.ucBlockOpt = ucBlockOpt;
    ptQ->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
    
    return OS_ERROR_NONE;
}

Uint8 OsQPost(T_OsQ *ptQ, void *pMsg)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    if (ptQ->uiCount >= ptQ->uiLength)
    {
        OS_EXIT_CRITICAL();
        return OS_ERROR_Q_BUF_FULL;
    }
    
    *(ptQ->puiHead) = (Uint32)pMsg;
    ptQ->uiCount++;
    
    if (ptQ->puiHead == (ptQ->puiBufQ + ptQ->uiLength - 1))
    {
        ptQ->puiHead = ptQ->puiBufQ;
    }
    else
    {
        ptQ->puiHead++;
    }
    
    if (OS_EVENT_STATUS_PEND == ptQ->tEvent.ucStatus)
    {
        ptQ->tEvent.ucStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return OS_ERROR_NONE;
    }
    
    OS_EXIT_CRITICAL();
    
    return OS_ERROR_NONE;
}

void *OsQPend(T_OsQ *ptQ, Uint32 uiTimeOut)
{
    void *pMsg = NULL;
    
    OS_ALLOC_CRITICAL();
    
    if (0 == ptQ->uiCount)
    {
        OS_ENTER_CRITICAL();
        ptQ->tEvent.ucStatus = OS_EVENT_STATUS_PEND;

        g_ptCurrentTcb->uiTimeDly = uiTimeOut;
        g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptQ->tEvent);
        g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
        OS_EXIT_CRITICAL();
                
        OsSchedule();   /* os pend */
    }
    
    OS_ENTER_CRITICAL();
    if (ptQ->uiCount > 0)
    {
        pMsg = (void *)*(ptQ->puiTail);
        ptQ->uiCount--;
        
        if (ptQ->puiTail == (ptQ->puiBufQ + ptQ->uiLength - 1))
        {
            ptQ->puiTail = ptQ->puiBufQ;
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




/* Flag Create Post Pend */

void OsFlagCreate(T_OsFlag *ptFlag, Uint8 ucBlockOpt)
{
    ptFlag->tEvent.ucType = OS_EVENT_TYPE_FLAG;
    ptFlag->tEvent.ucBlockOpt = ucBlockOpt;
    
    ptFlag->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
}

void OsFlagPost(T_OsFlag *ptFlag)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    if (OS_EVENT_STATUS_PEND == ptFlag->tEvent.ucStatus)
    {
        ptFlag->tEvent.ucStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return ;
    }
    
    OS_EXIT_CRITICAL();
}

Uint8 OsFlagPend(T_OsFlag *ptFlag, Uint32 uiTimeOut)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    if (OS_EVENT_STATUS_READY == ptFlag->tEvent.ucStatus)
    {
        ptFlag->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
        
        OS_EXIT_CRITICAL();
        return OS_ERROR_NONE;
    }
    
    ptFlag->tEvent.ucStatus = OS_EVENT_STATUS_PEND;

    g_ptCurrentTcb->uiTimeDly = uiTimeOut;
    g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptFlag->tEvent);
    g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
    OS_EXIT_CRITICAL();
            
    OsSchedule();       /* os pend */
    
    OS_ENTER_CRITICAL();
    if (OS_EVENT_STATUS_READY == ptFlag->tEvent.ucStatus)
    {
        ptFlag->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
    }
    else
    {
        OS_EXIT_CRITICAL();
        return OS_ERROR_FLAG_TIMEOUT;
    }
    
    OS_EXIT_CRITICAL();
    
    return OS_ERROR_NONE;
}




/* Mutex Create Post Pend */
void OsMutexCreate(T_OsMutex *ptMutex)
{
    ptMutex->ucFlag = 1;
    
    ptMutex->tEvent.ucType = OS_EVENT_TYPE_MUTEX;
    ptMutex->tEvent.ucBlockOpt = OS_EVENT_OPT_BLOCK;
    
    ptMutex->tEvent.ucStatus = OS_EVENT_STATUS_PEND;
}

void OsMutexUnlock(T_OsMutex *ptMutex)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();

    ptMutex->ucFlag = 1;
    
    if (OS_EVENT_STATUS_PEND == ptMutex->tEvent.ucStatus)
    {
        ptMutex->tEvent.ucStatus = OS_EVENT_STATUS_READY;
        OS_EXIT_CRITICAL();
        OsSchedule();
        return ;
    }
    
    OS_EXIT_CRITICAL();
}

Uint8 OsMutexLock(T_OsMutex *ptMutex)
{
    OS_ALLOC_CRITICAL();
    
    if (0 == ptMutex->ucFlag)
    {
        OS_ENTER_CRITICAL();
        ptMutex->tEvent.ucStatus = OS_EVENT_STATUS_PEND;

        g_ptCurrentTcb->ptEvent = (T_OsEvent*)&(ptMutex->tEvent);
        g_ptCurrentTcb->uiStatus = OS_TASK_STAT_PEND_EVENT;
        OS_EXIT_CRITICAL();
        
        OsSchedule();   /* os pend */
    }
    
    OS_ENTER_CRITICAL();
    if (1 == ptMutex->ucFlag)
    {
        ptMutex->ucFlag = 0;
    }
    else
    {
        OS_EXIT_CRITICAL();
        return OS_ERROR_MUTEX_TIMEOUT;
    }
    
    OS_EXIT_CRITICAL();
    
    return OS_ERROR_NONE;
}



/**************************************************************************/

Uint32 OsGetTimeTickMsCnt(void)
{
    return g_uiOsTimeTickMsCnt;
}
Uint32 OsGetTimeTickSecCnt(void)
{
    return g_uiOsTimeTickSecCnt;
}
static void OsSetTimeTickSecCnt(Uint32 uiTimeS)
{
    OS_ALLOC_CRITICAL();
    
    OS_ENTER_CRITICAL();
    
    g_uiOsTimeTickSecCnt = uiTimeS;
    g_uiOsTimeTickMsCnt = 0;
    
    OS_EXIT_CRITICAL();
}
Uint32 OsGetSysRunTimeSec(void)
{
    return g_uiOsRunTimeSec;
}

/*******************************************************************************
* system software clock
*******************************************************************************/

struct LnxTime 
{
	Uint32 uiSec;
	Uint32 uiMin;
	Uint32 uiHour;
	Uint32 uiMday;
	Uint32 uiMon;
	Uint32 uiYear;
	Uint32 uiWday;
	Uint32 uiYday;
};

static const Uint8 g_aucRtcDaysInMonth[12] = 
{
	31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
};

#define LEAPS_THRU_END_OF(y) ((y)/4 - (y)/100 + (y)/400)

static inline Uint8 IsLeapYear(Uint32 uiYear)
{
	return (!(uiYear % 4) && (uiYear % 100)) || !(uiYear % 400);
}

/* The number of days in the month. */
static inline Uint32 RtcMonthDays(Uint32 uiMonth, Uint32 uiYear)
{
	return g_aucRtcDaysInMonth[uiMonth] + (IsLeapYear(uiYear) && (uiMonth == 1));
}

/* Convert seconds since 01-01-1970 00:00:00 to Gregorian date. */
static inline void RtcTimeToTm(Uint32 uiTime, struct LnxTime *tm)
{
	Uint32 uiMonth = 0;
    Uint32 uiYear = 0;
	Sint32 iDays = 0;
    Sint32 iNewDays = 0;

	iDays = uiTime / 86400;
	uiTime -= (Uint32) iDays * 86400;

	/* day of the week, 1970-01-01 was a Thursday */
	tm->uiWday = (iDays + 4) % 7;

	uiYear = 1970 + iDays / 365;
	iDays -= (uiYear - 1970) * 365
		+ LEAPS_THRU_END_OF(uiYear - 1)
		- LEAPS_THRU_END_OF(1970 - 1);
	if (iDays < 0) 
    {
		uiYear -= 1;
		iDays += 365 + IsLeapYear(uiYear);
	}
	tm->uiYear = uiYear - 1900;
	tm->uiYday = iDays + 1;

	for (uiMonth = 0; uiMonth < 11; uiMonth++) 
    {
        iNewDays = iDays - RtcMonthDays(uiMonth, uiYear);
		if (iNewDays < 0)
        {
            break;
        }
		iDays = iNewDays;
	}
	tm->uiMon = uiMonth;
	tm->uiMday = iDays + 1;

	tm->uiHour = uiTime / 3600;
	uiTime -= tm->uiHour * 3600;
	tm->uiMin = uiTime / 60;
	tm->uiSec = uiTime - tm->uiMin * 60;
}

static inline void TimeSToSysTime(Uint32 uiTimeS, T_Time *ptTm)
{
    struct LnxTime tm;
    
    RtcTimeToTm(uiTimeS, &tm);
    
    ptTm->ucSec   = tm.uiSec ;
    ptTm->ucMin   = tm.uiMin ;
    ptTm->ucHour  = tm.uiHour;
    ptTm->ucDay   = tm.uiMday;
    ptTm->ucMon   = tm.uiMon + 1;
    ptTm->ucYear  = tm.uiYear - 100;
    ptTm->ucWkDay = tm.uiWday;
}


/* Converts Gregorian date to seconds since 1970-01-01 00:00:00.
 * Assumes input in normal date format, i.e. 1980-12-31 23:59:59
 * => year=1980, mon=12, day=31, hour=23, min=59, sec=59.
 *
 * [For the Julian calendar (which was used in Russia before 1917,
 * Britain & colonies before 1752, anywhere else before 1582,
 * and is still in use by some communities) leave out the
 * -year/100+year/400 terms, and add 10.]
 *
 * This algorithm was first published by Gauss (I think).
 *
 * WARNING: this function will overflow on 2106-02-07 06:28:16 on
 * machines where long is 32-bit! (However, as time_t is signed, we
 * will already get problems at other places on 2038-01-19 03:14:08)
 */
static inline Uint32 MkTime(const Uint32 uiYear0, const Uint32 uiMon0, \
       const Uint32 uiDay, const Uint32 uiHour, \
       const Uint32 uiMin, const Uint32 uiSec)
{
	Uint32 uiMon = uiMon0, uiYear = uiYear0;

	/* 1..12 -> 11,12,1..10 */
	if (0 >= (Sint32)(uiMon -= 2)) 
    {
		uiMon += 12;	/* Puts Feb last since it has leap day */
		uiYear -= 1;
	}

	return ((((Uint32)
		  (uiYear/4 - uiYear/100 + uiYear/400 + 367*uiMon/12 + uiDay) +
		  uiYear*365 - 719499
	    )*24 + uiHour /* now have hours */
	  )*60 + uiMin /* now have minutes */
	)*60 + uiSec; /* finally seconds */
}


/*
 * Convert Gregorian date to seconds since 01-01-1970 00:00:00.
 */
static inline Uint32 SysTimeToTimeS(T_Time *ptTm)
{
	struct LnxTime tm;
    
    tm.uiSec   = ptTm->ucSec;
	tm.uiMin   = ptTm->ucMin;
	tm.uiHour  = ptTm->ucHour;
	tm.uiMday  = ptTm->ucDay;
	tm.uiMon   = ptTm->ucMon - 1;
	tm.uiYear  = ptTm->ucYear + 100;
	tm.uiWday  = ptTm->ucWkDay;
    
    return MkTime(tm.uiYear + 1900, tm.uiMon + 1, tm.uiMday,
			tm.uiHour, tm.uiMin, tm.uiSec);
}

void OsGetSysTime(T_Time *ptTm)
{
    TimeSToSysTime(OsGetTimeTickSecCnt(), ptTm);
}

void OsSetSysTime(T_Time *ptTm)
{
    OsSetTimeTickSecCnt(SysTimeToTimeS(ptTm));
}


/*******************************************************************************/



