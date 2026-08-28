
#include "Common.h"

/* Saved register set structure. */
typedef struct
{
	Uint32 R0;
    Uint32 R1;
    Uint32 R2;
    Uint32 R3;
    Uint32 R4;
    Uint32 R5;
    Uint32 R6;
    Uint32 R7;
    Uint32 R8;
    Uint32 R9;
    Uint32 R10;
    Uint32 R11;
    Uint32 R12;
    Uint32 R13;
    Uint32 R14;
    Uint32 R15;
    Uint32 S0;
    Uint32 S1;
    Uint32 S2;
    Uint32 S3;
    Uint32 S4;
    Uint32 S5;
    Uint32 S6;
    Uint32 S7;
    Uint32 S8;
    Uint32 S9;
    Uint32 S10;
    Uint32 S11;
    Uint32 S12;
    Uint32 S13;
    Uint32 S14;
    Uint32 S15;

    Uint32 R0_3;
    Uint32 S0_3;
    Uint32 R4_7;
    Uint32 S4_7;
    Uint32 R8_11;
    Uint32 S8_11;
    Uint32 R12_15;
    Uint32 S12_15;

    Uint32 MR0F;
	Uint32 MR1F;
	Uint32 MR2F;
	Uint32 MR0B;
	Uint32 MR1B;
	Uint32 MR2B;

	Uint32 MS0F;
	Uint32 MS1F;
	Uint32 MS2F;
	Uint32 MS0B;
	Uint32 MS1B;
	Uint32 MS2B;

	Uint32 I0;
	Uint32 I1;
	Uint32 I2;
	Uint32 I3;
    Uint32 I4;
	Uint32 I5;
    Uint32 I6;
  //    Uint32 I7; I7 (SP) is stored in the task control block, so we don't need to store it here
	Uint32 I8;
	Uint32 I9;
	Uint32 I10;
	Uint32 I11;
    Uint32 I13;
    Uint32 I12;
	Uint32 I14;
	Uint32 I15;

	Uint32 M0;
	Uint32 M1;
	Uint32 M2;
	Uint32 M3;
    Uint32 M4;
    Uint32 M5;
    Uint32 M6;
    Uint32 M7;
	Uint32 M8;
	Uint32 M9;
	Uint32 M10;
	Uint32 M11;
    Uint32 M12;
    Uint32 M13;
    Uint32 M14;
    Uint32 M15;

	Uint32 B0;
	Uint32 B1;
	Uint32 B2;
	Uint32 B3;
    Uint32 B4;
	Uint32 B5;
    Uint32 B6;
    Uint32 B7;
	Uint32 B8;
	Uint32 B9;
	Uint32 B10;
	Uint32 B11;
    Uint32 B12;
    Uint32 B13;
	Uint32 B14;
	Uint32 B15;

    Uint32 L15;
    Uint32 L14;
    Uint32 L13;
    Uint32 L12;
    Uint32 L11;
    Uint32 L10;
    Uint32 L9;
    Uint32 L8;
    Uint32 L7;
    Uint32 L6;
    Uint32 L5;
    Uint32 L4;
    Uint32 L3;
    Uint32 L2;
    Uint32 L1;
    Uint32 L0;

    Uint32 BitFIFO_1;
	Uint32 BitFIFO_0;
	Uint32 BitFIFOWRP;

	Uint32 ASTATy;
    Uint32 ASTATx;
    Uint32 STKYy;
    Uint32 STKYx;
    Uint32 MODE1;
    Uint32 USTAT4;
    Uint32 USTAT3;
    Uint32 USTAT2;
    Uint32 USTAT1;

    Uint32 PX2;
    Uint32 PX1;
 //   Uint32 RTI;                 /* Saved by the RTL on interrupt entry - Sequence must not be changed */
 
} ContextRecord;


/* This is a (fake) structure that is only used to emulate a saved
 * context that does not have any hardware stack usage.  Only used
 * when initialising a task. */
typedef struct
{
	Uint32 LOOP_STACK_COUNT;
	Uint32 LCNTR;
	Uint32 PC_STACK_COUNT;
	Uint32 PC_STACK;
	
} StackRecord;



