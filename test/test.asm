
./test/test:     file format elf64-littleriscv


Disassembly of section .plt:

00000000000103c0 <_PROCEDURE_LINKAGE_TABLE_>:
   103c0:	.#..3..A......C.
   103d0:	.....S......g...

00000000000103e0 <__libc_start_main@plt>:
   103e0:	auipc	t3,0x2
   103e4:	ld	t3,-976(t3) # 12010 <__libc_start_main@GLIBC_2.34>
   103e8:	jalr	t1,t3
   103ec:	nop

Disassembly of section .text:

00000000000103f0 <_start>:
   103f0:	jal	10412 <load_gp>
   103f4:	mv	a5,a0
   103f6:	auipc	a0,0x0
   103fa:	add	a0,a0,234 # 104e0 <main>
   103fe:	ld	a1,0(sp)
   10400:	add	a2,sp,8
   10402:	and	sp,sp,-16
   10406:	li	a3,0
   10408:	li	a4,0
   1040a:	mv	a6,sp
   1040c:	jal	103e0 <__libc_start_main@plt>
   10410:	ebreak

0000000000010412 <load_gp>:
   10412:	auipc	gp,0x2
   10416:	add	gp,gp,1006 # 12800 <__global_pointer$>
   1041a:	ret
	...

000000000001041e <deregister_tm_clones>:
   1041e:	lui	a0,0x12
   10420:	lui	a4,0x12
   10422:	mv	a5,a0
   10426:	mv	a4,a4
   1042a:	beq	a4,a5,1043a <deregister_tm_clones+0x1c>
   1042e:	li	a5,0
   10432:	beqz	a5,1043a <deregister_tm_clones+0x1c>
   10434:	mv	a0,a0
   10438:	jr	a5
   1043a:	ret

000000000001043c <register_tm_clones>:
   1043c:	lui	a0,0x12
   1043e:	mv	a4,a0
   10442:	lui	a5,0x12
   10444:	mv	a5,a5
   10448:	sub	a5,a5,a4
   1044a:	sra	a5,a5,0x3
   1044c:	srl	a1,a5,0x3f
   10450:	add	a1,a1,a5
   10452:	sra	a1,a1,0x1
   10454:	beqz	a1,10462 <register_tm_clones+0x26>
   10456:	li	a5,0
   1045a:	beqz	a5,10462 <register_tm_clones+0x26>
   1045c:	mv	a0,a0
   10460:	jr	a5
   10462:	ret

0000000000010464 <__do_global_dtors_aux>:
   10464:	add	sp,sp,-16
   10466:	sd	s0,0(sp)
   10468:	lbu	a5,-2008(gp) # 12028 <completed.0>
   1046c:	sd	ra,8(sp)
   1046e:	bnez	a5,1047a <__do_global_dtors_aux+0x16>
   10470:	jal	1041e <deregister_tm_clones>
   10474:	li	a5,1
   10476:	sb	a5,-2008(gp) # 12028 <completed.0>
   1047a:	ld	ra,8(sp)
   1047c:	ld	s0,0(sp)
   1047e:	add	sp,sp,16
   10480:	ret

0000000000010482 <frame_dummy>:
   10482:	j	1043c <register_tm_clones>

0000000000010484 <a>:
   10484:	add	sp,sp,-48
   10486:	sd	ra,40(sp)
   10488:	sd	s0,32(sp)
   1048a:	add	s0,sp,48
   1048c:	mv	a5,a0
   1048e:	sw	a5,-36(s0)
   10492:	sw	zero,-20(s0)
   10496:	lw	a5,-36(s0)
   1049a:	mv	a3,a5
   1049c:	sext.w	a4,a3
   104a0:	lui	a5,0x66666
   104a4:	add	a5,a5,1639 # 66666667 <__global_pointer$+0x66653e67>
   104a8:	mul	a5,a4,a5
   104ac:	srl	a5,a5,0x20
   104ae:	sraw	a5,a5,0x2
   104b2:	mv	a4,a5
   104b4:	sraw	a5,a3,0x1f
   104b8:	subw	a5,a4,a5
   104bc:	sw	a5,-36(s0)
   104c0:	lw	a5,-20(s0)
   104c4:	addw	a5,a5,1
   104c6:	sw	a5,-20(s0)
   104ca:	lw	a5,-36(s0)
   104ce:	sext.w	a5,a5
   104d0:	bnez	a5,10496 <a+0x12>
   104d2:	lw	a5,-20(s0)
   104d6:	mv	a0,a5
   104d8:	ld	ra,40(sp)
   104da:	ld	s0,32(sp)
   104dc:	add	sp,sp,48
   104de:	ret

00000000000104e0 <main>:
   104e0:	add	sp,sp,-32
   104e2:	sd	ra,24(sp)
   104e4:	sd	s0,16(sp)
   104e6:	add	s0,sp,32
   104e8:	li	a5,10
   104ea:	sw	a5,-28(s0)
   104ee:	li	a5,59
   104f2:	sw	a5,-32(s0)
   104f6:	li	a5,1
   104f8:	sw	a5,-24(s0)
   104fc:	j	10534 <main+0x54>
   104fe:	lw	a5,-28(s0)
   10502:	mv	a4,a5
   10504:	lw	a5,-24(s0)
   10508:	remw	a5,a4,a5
   1050c:	sext.w	a5,a5
   1050e:	bnez	a5,1052a <main+0x4a>
   10510:	lw	a5,-32(s0)
   10514:	mv	a4,a5
   10516:	lw	a5,-24(s0)
   1051a:	remw	a5,a4,a5
   1051e:	sext.w	a5,a5
   10520:	bnez	a5,1052a <main+0x4a>
   10522:	lw	a5,-24(s0)
   10526:	sw	a5,-20(s0)
   1052a:	lw	a5,-24(s0)
   1052e:	addw	a5,a5,1
   10530:	sw	a5,-24(s0)
   10534:	lw	a5,-24(s0)
   10538:	mv	a4,a5
   1053a:	lw	a5,-28(s0)
   1053e:	sext.w	a4,a4
   10540:	sext.w	a5,a5
   10542:	blt	a5,a4,10558 <main+0x78>
   10546:	lw	a5,-24(s0)
   1054a:	mv	a4,a5
   1054c:	lw	a5,-32(s0)
   10550:	sext.w	a4,a4
   10552:	sext.w	a5,a5
   10554:	bge	a5,a4,104fe <main+0x1e>
   10558:	lw	a5,-20(s0)
   1055c:	mv	a0,a5
   1055e:	jal	10484 <a>
   10562:	mv	a5,a0
   10564:	mv	a0,a5
   10566:	ld	ra,24(sp)
   10568:	ld	s0,16(sp)
   1056a:	add	sp,sp,32
   1056c:	ret
