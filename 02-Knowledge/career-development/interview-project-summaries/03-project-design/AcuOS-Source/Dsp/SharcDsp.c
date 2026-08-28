/*******************************************************************************
* 文件名称：SharcDsp.c
* 文件说明：cpu platform
* 当前版本：V1.0
* 作 者：   hanwei
* 完成日期：2021-1-9
*******************************************************************************/
#include <builtins.h>                                      // sysreg_read
#include <sysreg.h>                                        // sysreg_MODE1
#include <sys/ADSP_SC573_cdef.h>                           // pREG_SEC0_RAISE
#include <sys/def215xx_core.h>                             // REGF_MODE1_BR0
#include "SharcDspAsm.h"                                   // ContextRecord

#include "AcuOs.h"

#define TASK_MODE1_CLR_BITS ((uint32_t)( \
	BITM_REGF_MODE1_BR0                | \
    BITM_REGF_MODE1_BR8                | \
    BITM_REGF_MODE1_SRCU               | \
	BITM_REGF_MODE1_SRD1L              | \
	BITM_REGF_MODE1_SRD2H              | \
	BITM_REGF_MODE1_SRD2L              | \
	BITM_REGF_MODE1_SRRFH              | \
	BITM_REGF_MODE1_SRRFL              | \
	BITM_REGF_MODE1_ALUSAT             | \
	BITM_REGF_MODE1_SSE                | \
	BITM_REGF_MODE1_TRUNCATE           | \
	BITM_REGF_MODE1_PEYEN              | \
	BITM_REGF_MODE1_BDCST9             | \
	BITM_REGF_MODE1_BDCST1             ) \
)

 /* tasks run in the secondary DAG and data regs */
#define TASK_MODE1_SET_BITS ((uint32_t)( \
	BITM_REGF_MODE1_CBUFEN             | \
	BITM_REGF_MODE1_SRRFL              | \
	BITM_REGF_MODE1_SRRFH              | \
	BITM_REGF_MODE1_SRD2L              | \
	BITM_REGF_MODE1_SRD2H              | \
	BITM_REGF_MODE1_SRD1L              | \
	BITM_REGF_MODE1_SRD1H              | \
	BITM_REGF_MODE1_IRPTEN             | \
	BITM_REGF_MODE1_RND32              ) \
)

extern T_OsTcb *g_ptCurrentTcb;
extern T_OsTcb *g_ptReadyTcb;

static Uint32 g_uiCpuSr = 0;
static Uint32 g_uiSavedIntMask = 0;

void vTaskSwitchContext(void)
{
	g_ptCurrentTcb = g_ptReadyTcb;
}


Uint32 OsEnterCritical(void)
{
	Uint32 uiMask  = sysreg_bit_tst(sysreg_MODE1, BITM_REGF_MODE1_IRPTEN);   \

	asm volatile("JUMP (PC, .SH_INT_DISABLED) (DB);  \n\
                                   BIT CLR MODE1 0x1000;     \n\
                                   NOP;                                      \n\
                                   .SH_INT_DISABLED: \n");

	g_uiCpuSr++;

	if (g_uiCpuSr == 1)
	{
		g_uiSavedIntMask = uiMask;
	}

	return (g_uiCpuSr);
}

void OsExitCritical(Uint32 uiCpuSr)
{
	g_uiCpuSr = uiCpuSr;

	g_uiCpuSr--;

	if (g_uiCpuSr == 0)
	{
		if (0u != g_uiSavedIntMask)
		{
			sysreg_bit_set(sysreg_MODE1, BITM_REGF_MODE1_IRPTEN);
		}
	}
}

void OsContextSwitchInt(void)
{
	/* Use SEC interrupts SOFT6 for SHARC0 (core 1) and SOFT7 for SHARC1 (core 2)
	 *
	 * 目前只支持SHARC  Core0
	 * */

	*pREG_SEC0_RAISE = INTR_SYS_SOFT6_INT;
}

Uint32 *OsTaskStkInit(void (*pTask)(void), Uint32 *puiStk, Uint32 uiStkSize)
{
	/* Load top of stack pointer */
    Uint32 *puiTos = puiStk + uiStkSize - 1;

    memset(puiStk, 0, (uiStkSize * 4));

	/* Simulate the stack frame as it would be created by a context
	 * switch interrupt.
	 */
    puiTos -= 4;                                    // space for arguments
    Uint32 *puiStkI6 = puiTos;
    puiTos -= 2;
	
    /* Allocate a context record on the task's stack */
    ContextRecord *pRec = (ContextRecord*)(puiTos);
    pRec -= 1;

    StackRecord *pStk = (StackRecord*)pRec;
    pStk -= 1;

    /* Initialize the context record */
	memset(pRec, 0, sizeof(ContextRecord));
	memset(pStk, 0, sizeof(StackRecord));

    /* Create the stack registers first */
    pRec->B6 = (Uint32)puiTos;
    pRec->B7 = (Uint32)puiTos;

	/* Set up the fixed registers */
	pRec->M6  =  1;
	pRec->M7  = (Uint32)-1;
	pRec->M14 =  1;
	pRec->M15 = (Uint32)-1;

    /* 任务传参(目前AcuOS系统不支持传参) */
    pRec->R4    = (Uint32)NULL;

    /* .. and the Run function. */
    pStk->PC_STACK = (Uint32)pTask;
    pStk->PC_STACK_COUNT = 1u;

    /* MODE1 is configured for a C runtime environment for new tasks.  */
    pRec->MODE1 = ((sysreg_read(sysreg_MODE1) & ~TASK_MODE1_CLR_BITS) |  TASK_MODE1_SET_BITS);

	/* Set the frame pointer to the top of stack */
	pRec->I6 = (Uint32)puiStkI6;

	/* Return the new stacktop */
	return (Uint32*)pStk;
}
