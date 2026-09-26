from pathlib import Path

def clean(line):
    line = line.split('//')[0]  # Remove comments
    line = line.strip() # Remove whitespace
    return line


file_path = input("Enter the path of the .asm file: ").strip('"')

input_path = Path(file_path)
output_path = input_path.with_suffix(".hack")



def instruction_type(instruction):

    if instruction.startswith("@"):
        return "A"

    return "C"

def translate_a_instruction(instruction):

    symbol = instruction[1:]

    if symbol.isdigit():
        value = int(symbol)
    else:
        value = resolve_vars(symbol)

    return format(value, "016b")


DEST = {
    None: "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111"
}

JUMP = {
    None: "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111"
}

COMP = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",

    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",

    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",

    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",

    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101"
}

# 111 | a | comp | dest | jump

def translate_c_instruction(instruction):
    dest, comp, jump = None, None, None

    if '=' in instruction:
        dest, instruction = instruction.split('=')
    if ';' in instruction:
        instruction, jump = instruction.split(';')

    comp = instruction

    return "111" + COMP.get(comp, "000") + DEST.get(dest, "000") + JUMP.get(jump, "000")


SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,

    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,

    "SCREEN": 16384,
    "KBD": 24576
}

def translate(instruction):
    if instruction.startswith("@"):
        return translate_a_instruction(instruction)
    else:
        return translate_c_instruction(instruction)


def find_labels(line, rom_address):

    cleaned = clean(line)

    if not cleaned:
        return rom_address

    if cleaned.startswith("(") and cleaned.endswith(")"):
        label = cleaned[1:-1]
        SYMBOLS[label] = rom_address
    else:
        rom_address += 1

    return rom_address


counter = 16

def resolve_vars(symbol):

    global counter

    if symbol not in SYMBOLS:
        SYMBOLS[symbol] = counter
        counter += 1

    return SYMBOLS[symbol]


rom_address = 0
count_lines = 0


with open(input_path, 'r') as file:

    # Pass 1
    for line in file:
        rom_address = find_labels(line, rom_address)

    file.seek(0)

    # Pass 2
    with open(output_path, 'w') as output:

        for line in file:

            cleaned = clean(line)

            if not cleaned:
                continue

            if cleaned.startswith("(") and cleaned.endswith(")"):
                continue

            binary_instruction = translate(cleaned)

            output.write(binary_instruction + "\n")
            count_lines += 1 
            print(cleaned)
            print(binary_instruction)
            print(count_lines)

with open(output_path, 'r+') as output:
    content = output.read()
    output.seek(0)

    if content.endswith("\n"):
        content = content[:-1]

    output.write(content)
    output.truncate()