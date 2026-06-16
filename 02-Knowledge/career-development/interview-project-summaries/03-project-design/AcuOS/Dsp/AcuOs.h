/**************************************************************************
* 文件名称：AcuOsCore.h
* 文件说明：AcuOsCore
* 版 本：   V1.01
* 作 者：   hanwei
* 日 期：   2019-08-01
*
**************************************************************************/
#ifndef ACU_OS_H
#define ACU_OS_H

#include "Common.h"


/*  user config  macro  */

#define OS_MAX_TASKS                    32                  /*   6 -- 25  for user  */
#define OS_MAX_TIMERS                   32                  
#define OS_MAX_ALARMS                   32   


#define OS_PER_SECOND_TICKS             1000				/*   100 000 -- 1   (10us -- 1S)  */
#define OS_TIMER_TICKS					10					/*   10 ticks  */


/*  system config  macro readonly */

#define OS_EVENT_OPT_BLOCK              1
#define OS_EVENT_OPT_NONE_BLOCK         2

#define OS_TIMER_MODE_ONCE              1
#define OS_TIMER_MODE_PERIOD			2


#define OS_ALLOC_CRITICAL()             Uint32 CpuSr = 0
#define OS_ENTER_CRITICAL()             (CpuSr = OsEnterCritical())
#define OS_EXIT_CRITICAL()              (OsExitCritical(CpuSr))




typedef struct OsEvent
{
    Uint8 ucType;
    Uint8 ucStatus;
    Uint8 ucBlockOpt;
    Uint8 ucExt;
    
} T_OsEvent;


typedef struct OsTcb
{
    Uint32 *puiStkTop;
    Uint32 *puiStkBot;
    Uint32 uiStkFree;
    
    Uint32 uiTimeDly;
    Uint32 uiPriority;
    Uint32 uiStatus;
    
    T_OsEvent *ptEvent;
    
    struct OsTcb *ptNext;
    
} T_OsTcb;

typedef struct OsTimer
{
    Uint8  ucEnable;
    Uint8  ucMode;
    Uint32 uiTimePeriod;
    Uint32 uiTimerDly;
    
	pFuncCallBackPtr pFunc;
    void  *pArg;
    
    struct OsTimer *ptNext;
	
} T_OsTimer;





extern Uint32 OsEnterCritical(void);
extern void OsExitCritical(Uint32 CpuSr);

extern void OsStartFirstTask(void);



Uint32 OsGetCpuUsagePercent(void);              /*   Cpu Usage Percent   0 - 100    */
Uint32 OsGetTaskCount(void);                    /*   task total count    */
Uint32 OsGetTimerCount(void);                   /*   timer total count    */


void OsContextSwitchInt(void);
Uint32 *OsTaskStkInit (void (*pTask)(void), Uint32 *puiStk, Uint32 uiStkSize);


Uint8 OsTaskCreate(void (*pTask)(void), T_OsTcb *ptOsTcb, Uint32 *puiStk, Uint32 uiStkSize, Uint32 uiPrio);
void OsTaskInit(void);
void OsTaskStart(void);



void OsTimeDlyMs(Uint32 uiMs);
void OsTimeTick(void);
void OsIntEnter(void);
void OsIntExit(void);

Uint8 OsTimerCreate(T_OsTimer *ptTimer, Uint32 uiTimeMs, Uint8 ucMode, pFuncCallBackPtr pFunc, void *pArg);
void OsTimerStart(T_OsTimer *ptTimer);
void OsTimerStop(T_OsTimer *ptTimer);


// -----------------------------------------------------------------------------


typedef struct OsSem
{
    T_OsEvent tEvent;
    
    Uint32 uiCnt;
    
} T_OsSem;



void OsSemCreate(T_OsSem *ptSem, Uint32 uiCntVal, Uint8 ucBlockOpt);
void OsSemPost(T_OsSem *ptSem);
Uint8 OsSemPend(T_OsSem *ptSem, Uint32 uiTimeOut);



// -----------------------------------------------------------------------------


typedef struct OsQ
{
    T_OsEvent tEvent;
    
    Uint32 *puiHead;
    Uint32 *puiTail;
    Uint32 *puiBufQ;
    
    Uint32 uiCount;
    Uint32 uiLength;
    
} T_OsQ;



Uint8 OsQCreate(T_OsQ *ptQ, Uint32 *apuiMsgBuf, Uint32 uiMsgBufLen, Uint8 ucBlockOpt);
Uint8 OsQPost(T_OsQ *ptQ, void *pMsg);
void *OsQPend(T_OsQ *ptQ, Uint32 uiTimeOut);



// -----------------------------------------------------------------------------



typedef struct OsFlag
{
    T_OsEvent tEvent;
    
} T_OsFlag;


void OsFlagCreate(T_OsFlag *ptFlag, Uint8 ucBlockOpt);
void OsFlagPost(T_OsFlag *ptFlag);
Uint8 OsFlagPend(T_OsFlag *ptFlag, Uint32 uiTimeOut);



// -----------------------------------------------------------------------------



typedef struct OsMutex
{
    T_OsEvent tEvent;
    Uint8 ucFlag;
    
} T_OsMutex;


void OsMutexCreate(T_OsMutex *ptMutex);
void OsMutexUnlock(T_OsMutex *ptMutex);
Uint8 OsMutexLock(T_OsMutex *ptMutex);



// -----------------------------------------------------------------------------

typedef struct Time
{
	Uint8 ucSec;
	Uint8 ucMin;
	Uint8 ucHour;
	Uint8 ucDay;
	Uint8 ucMon;
	Uint8 ucYear;
	Uint8 ucWkDay;
} T_Time;


Uint32 OsGetTimeTickMsCnt(void);                /*   get system ms count    */
Uint32 OsGetTimeTickSecCnt(void);               /*   get system second count    */

Uint32 OsGetSysRunTimeSec(void);                /*   get system runtime second    */

void OsGetSysTime(T_Time *ptTm);
void OsSetSysTime(T_Time *ptTm);

// -----------------------------------------------------------------------------

#define OS_ALARM_MODE_ONCE                  1
#define OS_ALARM_MODE_PERIOD_DAY			2
#define OS_ALARM_MODE_PERIOD_MONTH			3
#define OS_ALARM_MODE_PERIOD_YEAR			4
#define OS_ALARM_MODE_PERIOD_WKDAY			5

typedef struct OsAlarm
{
    Uint8  ucMode;
    T_Time tTime;
    
    Uint8  ucEnable;
	pFuncCallBackPtr pFunc;
    void  *pArg;
    
    struct OsAlarm *ptNext;
	
} T_OsAlarm;

Uint8 OsAlarmCreate(T_OsAlarm *ptAlarm, T_Time tTime, Uint8 ucMode, pFuncCallBackPtr pFunc, void *pArg);
void OsAlarmStart(T_OsAlarm *ptAlarm);
void OsAlarmStop(T_OsAlarm *ptAlarm);
void OsAlarmSet(T_OsAlarm *ptAlarm, T_Time tTime);
void OsTaskAlarmSecondCheck(void);

// -----------------------------------------------------------------------------




#define OS_ERROR_NONE                       0

#define OS_ERROR_TASK_MAX                   21
#define OS_ERROR_TASK_PRIO                  22

#define OS_ERROR_TIMER_MAX                  31

#define OS_ERROR_ALARM_MAX                  41


#define OS_ERROR_SEM_TIMEOUT                52

#define OS_ERROR_Q_BUF_NULL                 62
#define OS_ERROR_Q_BUF_FULL                 63

#define OS_ERROR_FLAG_TIMEOUT               72

#define OS_ERROR_MUTEX_TIMEOUT              82






#endif




