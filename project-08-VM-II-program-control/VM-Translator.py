import os
from pathlib import Path




def clean(line):
    line = line.split('//')[0]  # Remove comments
    line = line.strip() # Remove whitespace
    return line

def Parser(line):
    cleaned_line = clean(line)
    if not cleaned_line:
        return None
    parts = cleaned_line.split()
    command = parts[0]
    arg1 = parts[1] if len(parts) > 1 else None
    arg2 = parts[2] if len(parts) > 2 else None
    return command, arg1, arg2

COMMAND_TYPES = {
    "push": "C_PUSH",
    "pop": "C_POP",
    "label": "C_LABEL",
    "goto": "C_GOTO",
    "if-goto": "C_IF",
    "function": "C_FUNCTION",
    "call": "C_CALL",
    "return": "C_RETURN",
}

ARITHMETIC_COMMANDS = {
    "add", "sub", "neg", "eq", "gt", "lt",
    "and", "or", "not",
}

def command_type(command):
    if command in COMMAND_TYPES:
        return COMMAND_TYPES[command]
    elif command in ARITHMETIC_COMMANDS:
        return "C_ARITHMETIC"
    else:
        raise ValueError(f"Unknown VM command: {command}")


arithmetic_assembly = {

    "add": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D+M\n",

    "sub": "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n",

    "neg": "@SP\nA=M-1\nM=-M\n",

    "eq": "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@EQ_TRUE_{0}\nD;JEQ\n@SP\nA=M-1\nM=0\n@EQ_END_{0}\n0;JMP\n(EQ_TRUE_{0})\n@SP\nA=M-1\nM=-1\n(EQ_END_{0})\n",

    "gt": "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@GT_TRUE_{0}\nD;JGT\n@SP\nA=M-1\nM=0\n@GT_END_{0}\n0;JMP\n(GT_TRUE_{0})\n@SP\nA=M-1\nM=-1\n(GT_END_{0})\n",

    "lt": "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@LT_TRUE_{0}\nD;JLT\n@SP\nA=M-1\nM=0\n@LT_END_{0}\n0;JMP\n(LT_TRUE_{0})\n@SP\nA=M-1\nM=-1\n(LT_END_{0})\n",
    
    "and": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D&M\n",

    "or": "@SP\nAM=M-1\nD=M\nA=A-1\nM=D|M\n",

    "not": "@SP\nA=M-1\nM=!M\n"
}
 

def translate_arithmetic(command):
        translate_arithmetic.counter += 1
        return arithmetic_assembly[command].format(translate_arithmetic.counter)

translate_arithmetic.counter = 0

ASS = {
    "constant": "@{0}\nD=A\n",
    "part2": "@{0}\nD=M\n@{1}\nA=D+A\nD=M\n",
    "temp": "@{0}\nD=A\n@{1}\nA=D+A\nD=M\n",
    "static": "@{0}.{1}\nD=M\n",
    "push": "@SP\nA=M\nM=D\n@SP\nM=M+1\n\n"
}

LOCATION_BASES = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
    "temp": "5",
}


def translate_push(segment, index, input_path):
    if segment == "constant":
        return ASS[segment].format(index)  + ASS["push"]
    elif segment in ["local", "argument", "this", "that"]:
        base = LOCATION_BASES[segment]
        # return f"@{base}\nD=M\n@{index}\nA=D+A\nD=M\n" + ASS["push"]
        return ASS["part2"].format(base,index) + ASS["push"]
    elif segment == "temp":
        base = LOCATION_BASES[segment]
        # return f"@{base}\nD=A\n@{index}\nA=D+A\nD=M\n" + ASS["push"]
        return ASS["temp"].format(base,index) + ASS["push"]
    elif segment == "pointer":
        if index == "0":
            return "@THIS\nD=M\n" + ASS["push"]
        elif index == "1":
            return "@THAT\nD=M\n" + ASS["push"]
    elif segment == "static":
        return ASS["static"].format(input_path.stem, index) + ASS["push"]

def translate_pop(segment, index, input_path):
    if segment in ["local", "argument", "this", "that"]:
        base = LOCATION_BASES[segment]
        return f"@{base}\nD=M\n@{index}\nD=D+A\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n"
    elif segment == "temp":
        base = LOCATION_BASES[segment]
        return f"@{base}\nD=A\n@{index}\nD=D+A\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n"
    elif segment == "pointer":
        if index == "0":
            return "@SP\nAM=M-1\nD=M\n@THIS\nM=D\n"
        elif index == "1":
            return "@SP\nAM=M-1\nD=M\n@THAT\nM=D\n"
    elif segment == "static":
        return f"@SP\nAM=M-1\nD=M\n@{input_path.stem}.{index}\nM=D\n"

current_function = ""

def scoped_label(label):
    return f"{current_function}${label}" if current_function else label

def translate_label(label):
    return f"({scoped_label(label)})\n"

def translate_goto(label):
    return f"@{scoped_label(label)}\n0;JMP\n"

def translate_if_goto(label):
    return f"@SP\nAM=M-1\nD=M\n@{scoped_label(label)}\nD;JNE\n"

def translate_function(function_name, num_locals):
    global current_function
    current_function = function_name
    assembly_code = f"({function_name})\n"
    for _ in range(int(num_locals)):
        assembly_code += "@0\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"

    return assembly_code

count = 0

def translate_call(function_name, num_args):
    global count
    return_label = f"{function_name}$ret.{count}"
    count += 1
    save_state = (
        f"@{return_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"  # Push return address
        f"@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"  # Push LCL
        f"@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"  # Push ARG
        f"@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"  # Push THIS
        f"@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"  # Push THAT
        f"@SP\nD=M\n@5\nD=D-A\n@{num_args}\nD=D-A\n@ARG\nM=D\n"  # Reposition ARG
        f"@SP\nD=M\n@LCL\nM=D\n"  # Reposition LCL
    )

    jump_to_function = f"@{function_name}\n0;JMP\n"
    return_address_label = f"({return_label})\n"

    assembly_code = save_state + jump_to_function + return_address_label
    return assembly_code

def translate_return():
    assembly_code = (
        "@LCL\nD=M\n@R13\nM=D\n"  # FRAME = LCL
        "@5\nD=D-A\nA=D\nD=M\n@R14\nM=D\n"  # RET = *(FRAME-5)
        "@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n"  # *ARG = pop()
        "@ARG\nD=M+1\n@SP\nM=D\n"  # SP = ARG + 1
        "@R13\nAM=M-1\nD=M\n@THAT\nM=D\n"  # THAT = *(FRAME-1)
        "@R13\nAM=M-1\nD=M\n@THIS\nM=D\n"  # THIS = *(FRAME-2)
        "@R13\nAM=M-1\nD=M\n@ARG\nM=D\n"  # ARG = *(FRAME-3)
        "@R13\nAM=M-1\nD=M\n@LCL\nM=D\n"  # LCL = *(FRAME-4)
        "@R14\nA=M\n0;JMP\n"  # goto RET
    )
    return assembly_code

def write_arithmetic(command, asm_file):
    assembly_code = translate_arithmetic(command)
    asm_file.write(assembly_code)

def write_push_pop(command, segment, index, input_path, asm_file):
    if command == "push":
        assembly_code = translate_push(segment, index, input_path)
    elif command == "pop":
        assembly_code = translate_pop(segment, index, input_path)
    else:
        raise ValueError(f"Invalid memory command: {command}")

    asm_file.write(assembly_code)

def write_program_flow(command, label, asm_file):
    if command == "label":
        assembly_code = translate_label(label)
    elif command == "goto":
        assembly_code = translate_goto(label)
    elif command == "if-goto":
        assembly_code = translate_if_goto(label)
    else:
        raise ValueError(f"Invalid program flow command: {command}")
    
    asm_file.write(assembly_code)

def write_function_call_return(command, function_name, num, asm_file):
    if command == "function":
        assembly_code = translate_function(function_name, num)
    elif command == "call":
        assembly_code = translate_call(function_name, num)
    elif command == "return":
        assembly_code = translate_return()
    else:
        raise ValueError(f"Invalid function command: {command}")

    asm_file.write(assembly_code)

path = input("Enter the path of the .vm file or directory: ").strip().strip('"')

def read_path(path):
    path = Path(path)

    if path.is_file() and path.suffix == ".vm":
        return [path]

    elif path.is_dir():
        vm_files = sorted(path.glob("*.vm"))

        if not vm_files:
            raise ValueError("No .vm files found in the directory.")

        return vm_files

    else:
        raise ValueError("Enter a valid .vm file or directory.")

def get_output_path(path):
    path = Path(path)
    
    if path.is_file() and path.suffix == ".vm":
        return path.with_suffix(".asm")
    elif path.is_dir():
        return path / (path.name + ".asm")

input_paths = read_path(path)
output_path = get_output_path(path)

def write_bootstrap_code(asm_file):
    asm_file.write("@256\nD=A\n@SP\nM=D\n")  # Set SP to 256
    asm_file.write(translate_call("Sys.init", 0))  # Call Sys.init

with open(output_path, "w") as asm_file:
    asm_file.write("// This file is generated by VM-Translator.py Abo Bakr edition\n")
    asm_file.write("// written by Abo Bakr\n")
    asm_file.write("// spoof0x0 was here\n")
    asm_file.write("\n")

    if Path(path).is_dir():
        write_bootstrap_code(asm_file)

    for input_path in input_paths:
        with open(input_path, "r") as vm_file:
            for line in vm_file:
                parsed = Parser(line)

                if parsed:
                    command, arg1, arg2 = parsed
                    cmd_type = command_type(command)
                    if cmd_type == "C_ARITHMETIC":
                        write_arithmetic(command, asm_file)
                    elif cmd_type == "C_PUSH" or cmd_type == "C_POP":
                        write_push_pop(command, arg1, arg2, input_path, asm_file)
                    elif cmd_type == "C_LABEL" or cmd_type == "C_GOTO" or cmd_type == "C_IF":
                        write_program_flow(command, arg1, asm_file)
                    elif cmd_type == "C_FUNCTION" or cmd_type == "C_CALL" or cmd_type == "C_RETURN":
                        write_function_call_return(command, arg1, arg2, asm_file)
            