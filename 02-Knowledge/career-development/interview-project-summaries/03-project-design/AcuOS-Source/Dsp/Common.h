/************************************************************************
* 文件名称：Common.h
* 文件说明：commom
* 当前版本：V1.01
* 作 者：   hanwei
* 完成日期：2019-8-1
************************************************************************/
#ifndef         COMMON_H
#define         COMMON_H

typedef signed char             Sint8;
typedef signed short int        Sint16;
typedef signed int              Sint32;

typedef unsigned char           Uint8;
typedef unsigned short int      Uint16;
typedef unsigned int            Uint32;

typedef float                   Float;

typedef unsigned char           Bool;

typedef void (*pFuncCallBack)(void);
typedef void (*pFuncCallBackPtr)(void *pArg);

#define FALSE                   0
#define TRUE                    1

#define SUCCESS                 0
#define FAILURE                 1


#define BIT0                    0x0001
#define BIT1                    0x0002
#define BIT2                    0x0004
#define BIT3                    0x0008
#define BIT4                    0x0010
#define BIT5                    0x0020
#define BIT6                    0x0040
#define BIT7                    0x0080
#define BIT8                    0x0100
#define BIT9                    0x0200
#define BIT10                   0x0400
#define BIT11                   0x0800
#define BIT12                   0x1000
#define BIT13                   0x2000
#define BIT14                   0x4000
#define BIT15                   0x8000

#include <string.h>


#endif
