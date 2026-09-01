/**************************************************************************
* 文件名称：AcuOsCore.h
* 文件说明：AcuOsCore
* 版 本：   V1.01
* 作 者：   hanwei
* 日 期：   2018-08-01
*
**************************************************************************/
#ifndef ACU_OS_H
#define ACU_OS_H

#include "Common.h"

/*  user config  start  */

#define OS_TASK_STK_SIZE                64

#define OS_MAX_TASKS                    32
#define OS_MAX_EVENTS                   32
#define OS_MAX_Q_SIZE                   32

#define OS_PER_SECOND_TICKS             1000                  /*   100 000 -- 1   (10us -- 1S)  */




/*  system config  start  */

#define NVIC_INT_CTRL                   *(( volatile Uint32 *)0xE000ED04)
#define NVIC_PENDSV_SET                 0x10000000


#define OS_TASK_STAT_READY              1
#define OS_TASK_STAT_PEND_DLY           2
#define OS_TASK_STAT_PEND_EVENT         3


#define OS_EVENT_TYPE_SEM               1
#define OS_EVENT_TYPE_Q                 2

#define OS_EVENT_STATUS_PEND            1
#define OS_EVENT_STATUS_READY           2

#define OS_EVENT_OPT_BLOCK              1
#define OS_EVENT_OPT_NONE_BLOCK         2



#define OS_ALLOC_CRITICAL()             Uint32 CpuSr = 0
#define OS_ENTER_CRITICAL()             CpuSr = OsEnterCritical()
#define OS_EXIT_CRITICAL()              OsExitCritical(CpuSr)




typedef struct OsEvent{
    
    Uint32 uiType;
    Uint32 uiStatus;
    Uint32 uiBlockOpt;
    
}T_OsEvent;


typedef struct OsTcb{
    Uint32 *puiStk;
    
    Uint32 uiTimeDly;
    Uint32 uiPriority;
    Uint32 uiStatus;
    
    T_OsEvent *ptEvent;
    
}T_OsTcb;


extern Uint32 g_uiOsCpuUsage;



extern Uint32 OsEnterCritical(void);
extern void OsExitCritical(Uint32 CpuSr);

extern void OsStartFirstTask(void);






Uint8 OsTaskCreate(void (*pTask)(void), Uint32 *pTos, Uint32 uiPrio);
void OsTaskInit(void);
void OsTaskStart(void);



void OsTimeDlyMs(Uint32 uiMs);
void OsTimeTick(void);
void OsIntEnter(void);
void OsIntExit(void);




//------------------------------------------------------------------------------


typedef struct OsSem{
    
    T_OsEvent tEvent;
    
    Uint32 uiCnt;
    
}T_OsSem;



void OsSemCreate(T_OsSem *ptSem, Uint32 uiCntVal, Uint32 uiBlockOpt);
void OsSemPost(T_OsSem *ptSem);
void OsSemPend(T_OsSem *ptSem, Uint32 uiTimeOut);



//------------------------------------------------------------------------------


typedef struct OsQ{
    
    T_OsEvent tEvent;
    
    Uint32 *puiHead;
    Uint32 *puiTail;
    Uint32 *pauiBufQ[OS_MAX_Q_SIZE];
    
    Uint32 uiCount;
    Uint32 uiLength;
    
}T_OsQ;



void OsQCreate(T_OsQ *ptQ, Uint32 uiLength, Uint32 uiBlockOpt);
void OsQPost(T_OsQ *ptQ, void *pMsg);
void *OsQPend(T_OsQ *ptQ, Uint32 uiTimeOut);



//------------------------------------------------------------------------------








#define OS_ERROR_NONE                   0







#endif




