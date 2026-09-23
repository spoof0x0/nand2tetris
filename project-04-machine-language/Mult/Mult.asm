@R2  // result = 0
M=0

@i       // i = 0
M=0

@R0
D=M

@a       // a = R0
M=D

@R1
D=M 

@b       // b = R1
M=D

(CHECK)
@b 
D=M

@i
D=D-M

@LOOP
D;JGT

@END
0;JMP

(LOOP)
@R2
D=M

@a 
D=D+M 

@R2
M=D

@i
M=M+1

@CHECK
0;JMP

(STOP)
@STOP
0;JMP