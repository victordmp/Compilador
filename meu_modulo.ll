; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare void @"escrevaInteiro"(i32 %".1")

declare void @"escrevaFlutuante"(float %".1")

declare i32 @"leiaInteiro"()

declare float @"leiaFlutuante"()

define i32 @"maiorde2"(i32 %"x", i32 %"y")
{
bloco_entrada:
  %"se_entao" = icmp sgt i32 %"x", %"y"
  br i1 %"se_entao", label %"iftrue", label %"ifend"
iftrue:
  br label %"bloco_saida"
ifend:
  br label %"bloco_saida.1"
bloco_saida:
  ret i32 %"x"
bloco_saida.1:
  ret i32 %"y"
}

define i32 @"maiorde4"(i32 %"a", i32 %"b", i32 %"c", i32 %"d")
{
bloco_entrada:
  %".6" = call i32 @"maiorde2"(i32 %"a", i32 %"b")
  %".7" = call i32 @"maiorde2"(i32 %"c", i32 %"d")
  %".8" = call i32 @"maiorde2"(i32 %".6", i32 %".7")
  br label %"bloco_saida"
bloco_saida:
  ret i32 %".8"
}

define i32 @"main"()
{
bloco_entrada:
  %"A" = alloca i32, align 4
  %"B" = alloca i32, align 4
  %"C" = alloca i32, align 4
  %"D" = alloca i32, align 4
  %".2" = call i32 @"leiaInteiro"()
  store i32 %".2", i32* %"A", align 4
  %".4" = call i32 @"leiaInteiro"()
  store i32 %".4", i32* %"B", align 4
  %".6" = call i32 @"leiaInteiro"()
  store i32 %".6", i32* %"C", align 4
  %".8" = call i32 @"leiaInteiro"()
  store i32 %".8", i32* %"D", align 4
  %".10" = load i32, i32* %"A"
  %".11" = load i32, i32* %"B"
  %".12" = load i32, i32* %"C"
  %".13" = load i32, i32* %"D"
  %".14" = call i32 @"maiorde4"(i32 %".10", i32 %".11", i32 %".12", i32 %".13")
  call void @"escrevaInteiro"(i32 %".14")
  br label %"bloco_saida"
bloco_saida:
  ret i32 0
}
