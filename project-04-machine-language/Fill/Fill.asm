(LOOP)
@KBD
D=M

@BLACK
D;JNE

@WHITE
0;JMP

(BLACK)
@SCREEN
D=A

@i
M=D

(BLACK_LOOP)
@i
A=M
M=-1

@i
M=M+1
D=M

@24576
D=D-A

@BLACK_LOOP
D;JLT

@LOOP
0;JMP

(WHITE)
@SCREEN
D=A

@i
M=D

(WHITE_LOOP)
@i
A=M
M=0

@i
M=M+1
D=M

@24576
D=D-A

@WHITE_LOOP
D;JLT

@LOOP
0;JMP