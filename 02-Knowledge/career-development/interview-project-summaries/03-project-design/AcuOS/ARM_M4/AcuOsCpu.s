/**************************************************************************
* 文件名称：AcuOsCpu.s
* 文件说明：AcuOsCpu
* 版 本：   V1.01
* 作 者：   吴志亮
* 日 期：   2018-08-01
*
**************************************************************************/

    EXTERN      g_ptCurrentTcb
    EXTERN      g_ptReadyTcb

    PUBLIC      OsEnterCritical
    PUBLIC      OsExitCritical

    PUBLIC      OsStartFirstTask
    PUBLIC      OS_PendSV_Handler

    SECTION     CODE:CODE:NOROOT(2)
    THUMB

OsDisInt
    CPSID       I
    BX          LR
    
OsEnInt
    CPSIE       I
    BX          LR
    

OsEnterCritical
    MRS         R0, PRIMASK                     ; Set prio int mask to mask all (except faults)
    CPSID       I
    BX          LR
    
OsExitCritical
    MSR         PRIMASK, R0
    BX          LR


OsStartFirstTask

    CPSID       I
    
    MOVS        R0, #0x02
    MSR         CONTROL, R0                     ;set SP is PSP
    ISB
    
    LDR         R0, =g_ptReadyTcb               ;get the new tcb
    LDR         R1, [R0]                        ;get ptcb value
    LDR         R2, [R1]                        ;get ptcb stack
    MSR         PSP, R2                         ;restore PSP new top of stack
    
    MOV         R0, R2                          ;get the top of stack
    
    LDMIA       R0!, {R4-R11}                   ;restore R4-R11
    
    ADDS        R0, #16                         ;get PC,LR(R14),R12
    LDMIA       R0!,{R1-R3}
    MOV         R12,R1
    MOV         LR, R2
    ;           R3=PC
    LDMIA       R0!,{R3}                        ;get xPSR
    MSR         PSR,R3
    
    SUBS        R0, #32
    LDMIA       R0, {R0-R3}
    
    CPSIE       I
    
    BX          LR
    


OS_PendSV_Handler                               ;OSContextSwitch

    ; xPSR,PC,LR(R14),R12,R3-R0,  in proper oder, is be auto saved in stack
    
    CPSID       I
    
    MRS         R0, PSP
    
    SUBS        R0, #32
    STMIA       R0!,{R4-R11}                    ;save R4-R11, increment after
    
    SUBS        R0, #32
    MSR         PSP, R0                         ;save new stack position to PSP
    
    MRS         R0, PSP                         ;save PSP to current tcb stack
    LDR         R1, =g_ptCurrentTcb
    LDR         R2, [R1]
    STR         R0, [R2]
    
    ;---------------------------------------------------------------------------
    
    LDR         R0, =g_ptCurrentTcb             ;ptCurrent = ptReadyTcb
    LDR         R1, =g_ptReadyTcb
    LDR         R2, [R1]
    STR         R2, [R0]
    
    LDR         R0, [R2]                        ;get top of stack from ptReadyTcb
    LDMIA       R0!, {R4-R11}                   ;restore R4-R11, increment after
    
    MSR         PSP, R0                         ;restore PSP from ready task stk

    CPSIE       I
    BX          LR                              ;restore PC from LR value
    
    ; xPSR,PC,LR(R14),R12,R3-R0,  in proper oder, is be auto restored
    
    END
    
    