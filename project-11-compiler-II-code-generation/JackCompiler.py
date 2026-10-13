import re
import sys
from pathlib import Path
from SymbolTable import SymbolTable

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static", "var",
    "int", "char", "boolean", "void", "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
}
OPS = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
OP_VM = {
    "+": "add", "-": "sub", "&": "and", "|": "or",
    "<": "lt", ">": "gt", "=": "eq",
    "*": "call Math.multiply 2", "/": "call Math.divide 2",
}
KIND_SEGMENT = {"static": "static", "field": "this", "arg": "argument", "var": "local"}


def remove_comments(content):
    def repl(m):
        s = m.group(0)
        return s if s.startswith('"') else " "
    return re.sub(r'"[^"\n]*"|//[^\n]*|/\*.*?\*/', repl, content, flags=re.DOTALL)


def tokenize(text):
    text = remove_comments(text)
    pattern = r'"[^"\n]*"|[0-9]+|[A-Za-z_]\w*|[{}()[\].,;+\-*/&|<>=~]'
    return re.findall(pattern, text)


class VMWriter:
    def __init__(self, f):
        self.f = f

    def push(self, seg, i):
        self.f.write(f"push {seg} {i}\n")

    def pop(self, seg, i):
        self.f.write(f"pop {seg} {i}\n")

    def arithmetic(self, cmd):
        self.f.write(cmd + "\n")

    def label(self, l):
        self.f.write(f"label {l}\n")

    def goto(self, l):
        self.f.write(f"goto {l}\n")

    def if_goto(self, l):
        self.f.write(f"if-goto {l}\n")

    def call(self, name, n):
        self.f.write(f"call {name} {n}\n")

    def function(self, name, n):
        self.f.write(f"function {name} {n}\n")

    def ret(self):
        self.f.write("return\n")


class CompilationEngine:
    def __init__(self, tokens, out_file):
        self.t = tokens
        self.i = 0
        self.st = SymbolTable()  # fresh table per class (static/field counters start at 0)
        self.class_name = ""
        self.label_id = 0
        self.f = open(out_file, "w")
        self.vm = VMWriter(self.f)
        self.compile_class()
        self.f.close()

    # ---- helpers ----
    def peek(self):
        return self.t[self.i]

    def advance(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expect(self, tok):
        got = self.advance()
        if got != tok:
            raise SyntaxError(f"Expected '{tok}' but found '{got}'")

    def new_label(self, base):
        self.label_id += 1
        return f"{base}{self.label_id}"

    def push_var(self, name):
        self.vm.push(KIND_SEGMENT[self.st.kindOf(name)], self.st.indexOf(name))

    def pop_var(self, name):
        self.vm.pop(KIND_SEGMENT[self.st.kindOf(name)], self.st.indexOf(name))

    # ---- structure ----
    def compile_class(self):
        self.expect("class")
        self.class_name = self.advance()
        self.expect("{")
        while self.peek() in {"static", "field"}:
            self.compile_class_var_dec()
        while self.peek() in {"constructor", "function", "method"}:
            self.compile_subroutine()
        self.expect("}")

    def compile_class_var_dec(self):
        kind = self.advance()
        var_type = self.advance()
        self.st.define(self.advance(), var_type, kind)
        while self.peek() == ",":
            self.advance()
            self.st.define(self.advance(), var_type, kind)
        self.expect(";")

    def compile_subroutine(self):
        kind = self.advance()
        self.advance()  # return type
        name = self.advance()
        self.st.startSubroutine()
        if kind == "method":
            self.st.define("this", self.class_name, "arg")
        self.expect("(")
        self.compile_parameter_list()
        self.expect(")")
        self.expect("{")
        while self.peek() == "var":
            self.compile_var_dec()
        self.vm.function(f"{self.class_name}.{name}", self.st.varCount("var"))
        if kind == "constructor":
            self.vm.push("constant", self.st.varCount("field"))
            self.vm.call("Memory.alloc", 1)
            self.vm.pop("pointer", 0)
        elif kind == "method":
            self.vm.push("argument", 0)
            self.vm.pop("pointer", 0)
        self.compile_statements()
        self.expect("}")

    def compile_parameter_list(self):
        if self.peek() == ")":
            return
        while True:
            var_type = self.advance()
            self.st.define(self.advance(), var_type, "arg")
            if self.peek() == ",":
                self.advance()
            else:
                break

    def compile_var_dec(self):
        self.expect("var")
        var_type = self.advance()
        self.st.define(self.advance(), var_type, "var")
        while self.peek() == ",":
            self.advance()
            self.st.define(self.advance(), var_type, "var")
        self.expect(";")

    # ---- statements ----
    def compile_statements(self):
        while self.peek() in {"let", "if", "while", "do", "return"}:
            getattr(self, "compile_" + self.peek())()

    def compile_let(self):
        self.expect("let")
        name = self.advance()
        if self.peek() == "[":
            self.advance()
            self.push_var(name)
            self.compile_expression()
            self.expect("]")
            self.vm.arithmetic("add")
            self.expect("=")
            self.compile_expression()
            self.expect(";")
            self.vm.pop("temp", 0)
            self.vm.pop("pointer", 1)
            self.vm.push("temp", 0)
            self.vm.pop("that", 0)
        else:
            self.expect("=")
            self.compile_expression()
            self.expect(";")
            self.pop_var(name)

    def compile_if(self):
        else_l = self.new_label("IF_FALSE")
        end_l = self.new_label("IF_END")
        self.expect("if")
        self.expect("(")
        self.compile_expression()
        self.expect(")")
        self.vm.arithmetic("not")
        self.vm.if_goto(else_l)
        self.expect("{")
        self.compile_statements()
        self.expect("}")
        self.vm.goto(end_l)
        self.vm.label(else_l)
        if self.peek() == "else":
            self.advance()
            self.expect("{")
            self.compile_statements()
            self.expect("}")
        self.vm.label(end_l)

    def compile_while(self):
        top_l = self.new_label("WHILE_TOP")
        end_l = self.new_label("WHILE_END")
        self.expect("while")
        self.vm.label(top_l)
        self.expect("(")
        self.compile_expression()
        self.expect(")")
        self.vm.arithmetic("not")
        self.vm.if_goto(end_l)
        self.expect("{")
        self.compile_statements()
        self.expect("}")
        self.vm.goto(top_l)
        self.vm.label(end_l)

    def compile_do(self):
        self.expect("do")
        name = self.advance()
        self.compile_call(name)
        self.expect(";")
        self.vm.pop("temp", 0)

    def compile_return(self):
        self.expect("return")
        if self.peek() != ";":
            self.compile_expression()
        else:
            self.vm.push("constant", 0)
        self.expect(";")
        self.vm.ret()

    # ---- expressions ----
    def compile_expression(self):
        self.compile_term()
        while self.peek() in OPS:
            op = self.advance()
            self.compile_term()
            self.vm.arithmetic(OP_VM[op])

    def compile_term(self):
        tok = self.advance()
        if re.fullmatch(r"[0-9]+", tok):
            self.vm.push("constant", int(tok))
        elif tok.startswith('"'):
            s = tok[1:-1]
            self.vm.push("constant", len(s))
            self.vm.call("String.new", 1)
            for ch in s:
                self.vm.push("constant", ord(ch))
                self.vm.call("String.appendChar", 2)
        elif tok == "true":
            self.vm.push("constant", 0)
            self.vm.arithmetic("not")
        elif tok in {"false", "null"}:
            self.vm.push("constant", 0)
        elif tok == "this":
            self.vm.push("pointer", 0)
        elif tok == "(":
            self.compile_expression()
            self.expect(")")
        elif tok == "-":
            self.compile_term()
            self.vm.arithmetic("neg")
        elif tok == "~":
            self.compile_term()
            self.vm.arithmetic("not")
        else:  # identifier
            nxt = self.peek()
            if nxt == "[":
                self.advance()
                self.push_var(tok)
                self.compile_expression()
                self.expect("]")
                self.vm.arithmetic("add")
                self.vm.pop("pointer", 1)
                self.vm.push("that", 0)
            elif nxt in {".", "("}:
                self.compile_call(tok)
            else:
                self.push_var(tok)

    def compile_call(self, first):
        n_args = 0
        if self.peek() == ".":
            self.advance()
            sub = self.advance()
            if self.st.lookUp(first):  # method call on an object variable
                self.push_var(first)
                full = f"{self.st.typeOf(first)}.{sub}"
                n_args = 1
            else:  # function / constructor call: ClassName.sub
                full = f"{first}.{sub}"
        else:  # method call on current object
            self.vm.push("pointer", 0)
            full = f"{self.class_name}.{first}"
            n_args = 1
        self.expect("(")
        n_args += self.compile_expression_list()
        self.expect(")")
        self.vm.call(full, n_args)

    def compile_expression_list(self):
        count = 0
        if self.peek() != ")":
            self.compile_expression()
            count = 1
            while self.peek() == ",":
                self.advance()
                self.compile_expression()
                count += 1
        return count


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = [path] if path.is_file() else sorted(path.glob("*.jack"))
    for file in files:
        tokens = tokenize(file.read_text())
        CompilationEngine(tokens, str(file.with_suffix(".vm")))
        print(f"Compiled {file.name} -> {file.stem}.vm")


if __name__ == "__main__":
    main()
