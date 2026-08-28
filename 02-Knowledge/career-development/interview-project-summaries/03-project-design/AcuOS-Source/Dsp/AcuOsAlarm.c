/*******************************************************************************
* 文件名称：AcuOsAlarm.c
* 文件说明：闹钟
* 当前版本：V1.0
* 作 者：   hanwei
* 完成日期：2019-10-16
*******************************************************************************/
#include "AcuOs.h"

static T_OsAlarm *g_ptOsAlarmHead = NULL;
static Uint32 g_uiSysSecondBak = 0;


static Uint8 OsAlarmTotalCount(T_OsAlarm *ptAlarm)
{
    Uint8 ucCount = 0;
    
    T_OsAlarm *ptT = ptAlarm;
    
    while (NULL != ptT)
    {
        ucCount++;
        ptT = ptT->ptNext;
    }
    
    return ucCount;
}

static Uint8 OsAlarmCheckExist(T_OsAlarm *ptAlarm)
{
    T_OsAlarm *ptAlm = NULL;

    ptAlm = g_ptOsAlarmHead;
    
    while (NULL != ptAlm)
    {
        if (ptAlm == ptAlarm)
        {
            return 1;
        }
        
        ptAlm = ptAlm->ptNext;
    }
    
    return 0;
}

Uint8 OsAlarmCreate(T_OsAlarm *ptAlarm, T_Time tTime, Uint8 ucMode, pFuncCallBackPtr pFunc, void *pArg)
{
    T_OsAlarm *ptAlm = NULL;
    
    if (OsAlarmTotalCount(g_ptOsAlarmHead) > OS_MAX_ALARMS)
    {
        return OS_ERROR_ALARM_MAX;
    }
    
    if (OsAlarmCheckExist(ptAlarm) != 0)
    {
        return 2;
    }
    
    if (NULL == g_ptOsAlarmHead)
    {
        g_ptOsAlarmHead = ptAlarm;
		ptAlarm->ptNext = NULL;
    }
	else
	{
        ptAlm = g_ptOsAlarmHead;
		while (NULL != ptAlm->ptNext)
		{
			ptAlm = ptAlm->ptNext;
		}
		ptAlm->ptNext = ptAlarm;
		ptAlarm->ptNext = NULL;
	}
	
	ptAlarm->ucEnable = 0;
	ptAlarm->ucMode = ucMode;
    memcpy((Uint8*)&ptAlarm->tTime, (Uint8*)&tTime, sizeof(T_Time));
	ptAlarm->pFunc = pFunc;
    ptAlarm->pArg = pArg;
    
    return OS_ERROR_NONE;
}
void OsAlarmStart(T_OsAlarm *ptAlarm)
{
    ptAlarm->ucEnable = 1;
}
void OsAlarmStop(T_OsAlarm *ptAlarm)
{
	ptAlarm->ucEnable = 0;       
}
void OsAlarmSet(T_OsAlarm *ptAlarm, T_Time tTime)
{
    OsAlarmStop(ptAlarm);
    
    memcpy((Uint8*)&ptAlarm->tTime, (Uint8*)&tTime, sizeof(T_Time));
    
    OsAlarmStart(ptAlarm);
}


static inline void OsTaskAlarmUpProc(T_OsAlarm *ptAlarm)
{
    if (NULL != ptAlarm->pFunc)
    {
        ptAlarm->pFunc(ptAlarm->pArg);
    }
}

static void OsTaskAlarmListProc(T_OsAlarm *ptAlarm)
{
    T_Time tNowTime;
    
	T_OsAlarm *ptAlm = NULL;
    
    ptAlm = ptAlarm;
    
    if (NULL != ptAlm)
    {
        OsGetSysTime(&tNowTime);
        
        while (NULL != ptAlm)
        {
            if (1 == ptAlm->ucEnable)
            {
                if (OS_ALARM_MODE_ONCE == ptAlm->ucMode)
                {
                    if ((ptAlm->tTime.ucSec == tNowTime.ucSec) \
                        && (ptAlm->tTime.ucMin == tNowTime.ucMin) \
                        && (ptAlm->tTime.ucHour == tNowTime.ucHour) \
                        && (ptAlm->tTime.ucDay == tNowTime.ucDay) \
                        && (ptAlm->tTime.ucMon == tNowTime.ucMon) \
                        && (ptAlm->tTime.ucYear == tNowTime.ucYear))
                    {
                        OsTaskAlarmUpProc(ptAlm);
                        
                        ptAlm->ucEnable = 0;
                    }
                }
                else if (OS_ALARM_MODE_PERIOD_DAY == ptAlm->ucMode)
                {
                    if ((ptAlm->tTime.ucSec == tNowTime.ucSec) \
                        && (ptAlm->tTime.ucMin == tNowTime.ucMin) \
                        && (ptAlm->tTime.ucHour == tNowTime.ucHour))
                    {
                        OsTaskAlarmUpProc(ptAlm);
                    }
                }
                else if (OS_ALARM_MODE_PERIOD_MONTH == ptAlm->ucMode)
                {
                    if ((ptAlm->tTime.ucSec == tNowTime.ucSec) \
                        && (ptAlm->tTime.ucMin == tNowTime.ucMin) \
                        && (ptAlm->tTime.ucHour == tNowTime.ucHour) \
                        && (ptAlm->tTime.ucDay == tNowTime.ucDay))
                    {
                        OsTaskAlarmUpProc(ptAlm);
                    }
                }
                else if (OS_ALARM_MODE_PERIOD_YEAR == ptAlm->ucMode)
                {
                    if ((ptAlm->tTime.ucSec == tNowTime.ucSec) \
                        && (ptAlm->tTime.ucMin == tNowTime.ucMin) \
                        && (ptAlm->tTime.ucHour == tNowTime.ucHour) \
                        && (ptAlm->tTime.ucDay == tNowTime.ucDay) \
                        && (ptAlm->tTime.ucMon == tNowTime.ucMon))
                    {
                        OsTaskAlarmUpProc(ptAlm);
                    }
                }
                else if (OS_ALARM_MODE_PERIOD_WKDAY == ptAlm->ucMode)
                {
                    if ((ptAlm->tTime.ucSec == tNowTime.ucSec) \
                        && (ptAlm->tTime.ucMin == tNowTime.ucMin) \
                        && (ptAlm->tTime.ucHour == tNowTime.ucHour) \
                        && (ptAlm->tTime.ucWkDay == tNowTime.ucWkDay))
                    {
                        OsTaskAlarmUpProc(ptAlm);
                    }
                }
                else
                {
                    ptAlm->ucEnable = 0;
                }
            }
            
            ptAlm = ptAlm->ptNext;
        }
    }
}


void OsTaskAlarmSecondCheck(void)
{
    Uint32 uiTimeTick = 0;
    
    uiTimeTick = OsGetTimeTickSecCnt();
    
    if (g_uiSysSecondBak < uiTimeTick)
    {
        OsTaskAlarmListProc(g_ptOsAlarmHead);
    }
    
    g_uiSysSecondBak = uiTimeTick;
}

