
import sys
from pathlib import Path
import re



KEYWORDS = {
    "class", "constructor", "function", "method",
    "field", "static", "var",
    "int", "char", "boolean", "void",
    "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return"
}

SYMBOLS = set("{}()[].,;+-*/&|<>=~")

def JackAnalyzer():
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    fileORdir(path)

def fileORdir(path):
    path = Path(path)

    while not path.exists() or not (path.is_file() or path.is_dir()):
        path = Path(input("Please enter a valid directory or file path: "))

    files = [path] if path.is_file() else sorted(path.glob("*.jack"))

    for file in files:
        if file.suffix != ".jack":
            continue

        tokens = JackTokenizer(str(file))

        output_file = file.with_name(file.stem + ".xml")
        CompilationEngine(tokens, str(output_file))

def remove_comments(content):
    def repl(m):
        s = m.group(0)
        return s if s.startswith('"') else ' '
    return re.sub(r'"[^"\n]*"|//[^\n]*|/\*.*?\*/', repl, content, flags=re.DOTALL)

def JackTokenizer(file_path):
    with open(file_path, 'r') as rFile, open(file_path.replace('.jack', 'T.xml'), 'w') as wFile:
        content = rFile.read()
        content = remove_comments(content)
        pattern = r'"[^"\n]*"|[0-9]+|[A-Za-z_]\w*|[{}()[\].,;+\-*/&|<>=~]'
        tokens = re.findall(pattern, content)
        
        wFile.write("<tokens>\n")

        for token in tokens:
            token_type_str = token_type(token)
            value = token

            if token_type_str == "symbol":
                value = {
                    "<": "&lt;",
                    ">": "&gt;",
                    "&": "&amp;"
                }.get(token, token)

            wFile.write(
                f"<{token_type_str}> {value} </{token_type_str}>\n"
            )

        wFile.write("</tokens>\n")
    return tokens

def token_type(token):
    if token in KEYWORDS:
        return "keyword"
    elif token in SYMBOLS:
        return "symbol"
    elif re.match(r'^[0-9]+$', token):
        return "integerConstant"
    elif re.match(r'^"[^"\n]*"$', token):
        return "stringConstant"
    else:
        return "identifier"

class IndentWriter:
    def __init__(self, f):
        self.f = f
        self.level = 0

    def write(self, line):
        line = line.strip()
        if line.startswith("</"):          # closing tag: ارجع خطوة قبل الكتابة
            self.level -= 1
        self.f.write("  " * self.level + line + "\n")
        if re.fullmatch(r"<\w+>", line):   # opening tag فاضي: انزل مستوى
            self.level += 1

def CompilationEngine(tokens, output_file):
    index = 0

    def compile_class():
        nonlocal index

        # class
        if index < len(tokens) and tokens[index] == "class":
            wFile.write("<class>\n")
            wFile.write(f"<keyword> {tokens[index]} </keyword>\n")
            index += 1
        else:
            raise SyntaxError("Expected 'class'")

        # Class name
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected class name")

        # Opening brace
        if index < len(tokens) and tokens[index] == "{":
            wFile.write("<symbol> { </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '{'")

        # Class variables and subroutines
        while index < len(tokens) and tokens[index] != "}":
            if tokens[index] in {"static", "field"}:
                compile_class_var_dec()
            elif tokens[index] in {"constructor", "function", "method"}:
                compile_subroutine_dec()
            else:
                raise SyntaxError(f"Unexpected token: {tokens[index]}")

        # Closing brace
        if index < len(tokens) and tokens[index] == "}":
            wFile.write("<symbol> } </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '}'")

        wFile.write("</class>\n")

    def compile_class_var_dec():
        nonlocal index

        wFile.write("<classVarDec>\n")

        # static or field
        if index < len(tokens) and tokens[index] in {"static", "field"}:
            wFile.write(f"<keyword> {tokens[index]} </keyword>\n")
            index += 1
        else:
            raise SyntaxError("Expected 'static' or 'field'")

        # Type
        if index < len(tokens) and tokens[index] in {
            "int", "char", "boolean"
        }:
            wFile.write(f"<keyword> {tokens[index]} </keyword>\n")
            index += 1
        elif index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected variable type")

        # First variable name
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected variable name")

        # Additional variable names
        while index < len(tokens) and tokens[index] == ",":
            write_symbol(tokens[index])
            index += 1

            if index < len(tokens) and token_type(tokens[index]) == "identifier":
                wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
                index += 1
            else:
                raise SyntaxError("Expected variable name after ','")

        # Semicolon
        if index < len(tokens) and tokens[index] == ";":
            write_symbol(tokens[index])
            index += 1
        else:
            raise SyntaxError("Expected ';'")

        wFile.write("</classVarDec>\n")

    def compile_subroutine_dec():
        nonlocal index

        wFile.write("<subroutineDec>\n")

        # Subroutine type
        if index < len(tokens) and tokens[index] in {
            "constructor", "function", "method"
        }:
            wFile.write(f"<keyword> {tokens[index]} </keyword>\n")
            index += 1
        else:
            raise SyntaxError(
                "Expected constructor, function, or method"
            )

        # Return type
        if index < len(tokens) and tokens[index] in {
            "void", "int", "char", "boolean"
        }:
            wFile.write(f"<keyword> {tokens[index]} </keyword>\n")
            index += 1
        elif index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected return type")

        # Subroutine name
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected subroutine name")

        # Opening parenthesis
        if index < len(tokens) and tokens[index] == "(":
            wFile.write("<symbol> ( </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '('")

        # Parameter list
        compile_parameter_list()

        # Closing parenthesis
        if index < len(tokens) and tokens[index] == ")":
            wFile.write("<symbol> ) </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ')'")

        compile_subroutine_body()

        wFile.write("</subroutineDec>\n")

    def compile_subroutine_body():
        nonlocal index

        wFile.write("<subroutineBody>\n")

        # Opening brace
        if index < len(tokens) and tokens[index] == "{":
            wFile.write("<symbol> { </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '{'")

        while index < len(tokens) and tokens[index] == "var":
             compile_var_dec()

        # Statements
        compile_statements()

        # Closing brace
        if index < len(tokens) and tokens[index] == "}":
            wFile.write("<symbol> } </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '}'")

        wFile.write("</subroutineBody>\n")

    def compile_statements():
        nonlocal index

        wFile.write("<statements>\n")

        statements = {
            "let": compile_letStatements,
            "if": compile_ifStatements,
            "while": compile_whileStatements,
            "do": compile_doStatement,
        }

        while index < len(tokens) and tokens[index] in {
            "let", "if", "while", "do", "return"
        }:
            if tokens[index] == "return":
                compile_returnStatement()
            elif tokens[index] in statements:
                statements[tokens[index]]()
            else:
                raise SyntaxError(
                    f"Statement not implemented: {tokens[index]}"
                )

        wFile.write("</statements>\n")

    def compile_letStatements():
        nonlocal index

        wFile.write("<letStatement>\n")

        # let
        wFile.write("<keyword> let </keyword>\n")
        index += 1

        # Variable name
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected variable name")

        # Optional array indexing
        if index < len(tokens) and tokens[index] == "[":
            wFile.write("<symbol> [ </symbol>\n")
            index += 1
            compile_expression()

            if index < len(tokens) and tokens[index] == "]":
                wFile.write("<symbol> ] </symbol>\n")
                index += 1
            else:
                raise SyntaxError("Expected ']'")

        # =
        if index < len(tokens) and tokens[index] == "=":
            wFile.write("<symbol> = </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '='")

        # Expression
        compile_expression()

        # ;
        if index < len(tokens) and tokens[index] == ";":
            wFile.write("<symbol> ; </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ';'")

        wFile.write("</letStatement>\n")

    def compile_ifStatements():
        nonlocal index

        wFile.write("<ifStatement>\n")

        # if
        wFile.write("<keyword> if </keyword>\n")
        index += 1

        # (
        if index < len(tokens) and tokens[index] == "(":
            wFile.write("<symbol> ( </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '(' after if")

        compile_expression()

        # )
        if index < len(tokens) and tokens[index] == ")":
            wFile.write("<symbol> ) </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ')' after condition")

        # {
        if index < len(tokens) and tokens[index] == "{":
            wFile.write("<symbol> { </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '{' after if condition")

        compile_statements()

        # }
        if index < len(tokens) and tokens[index] == "}":
            wFile.write("<symbol> } </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '}' after if body")

        # Optional else
        if index < len(tokens) and tokens[index] == "else":
            wFile.write("<keyword> else </keyword>\n")
            index += 1

            if index < len(tokens) and tokens[index] == "{":
                wFile.write("<symbol> { </symbol>\n")
                index += 1
            else:
                raise SyntaxError("Expected '{' after else")

            compile_statements()

            if index < len(tokens) and tokens[index] == "}":
                wFile.write("<symbol> } </symbol>\n")
                index += 1
            else:
                raise SyntaxError("Expected '}' after else body")

        wFile.write("</ifStatement>\n")

    def compile_whileStatements():
        nonlocal index

        wFile.write("<whileStatement>\n")

        # while
        wFile.write("<keyword> while </keyword>\n")
        index += 1

        # (
        if index < len(tokens) and tokens[index] == "(":
            wFile.write("<symbol> ( </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '(' after while")

        compile_expression()

        # )
        if index < len(tokens) and tokens[index] == ")":
            wFile.write("<symbol> ) </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ')' after condition")

        # {
        if index < len(tokens) and tokens[index] == "{":
            wFile.write("<symbol> { </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '{' after while condition")

        compile_statements()

        # }
        if index < len(tokens) and tokens[index] == "}":
            wFile.write("<symbol> } </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '}' after while body")

        wFile.write("</whileStatement>\n")

    def compile_returnStatement():
        nonlocal index

        wFile.write("<returnStatement>\n")

        wFile.write("<keyword> return </keyword>\n")
        index += 1

        if index < len(tokens) and tokens[index] != ";":
            compile_expression()

        if index < len(tokens) and tokens[index] == ";":
            wFile.write("<symbol> ; </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ';' after return")

        wFile.write("</returnStatement>\n")

    def compile_expression():
        nonlocal index

        wFile.write("<expression>\n")

        # First term
        compile_term()

        # Operators
        operators = {
            "+", "-", "*", "/", "&", "|",
            "<", ">", "="
        }

        while index < len(tokens) and tokens[index] in operators:
            write_symbol(tokens[index])
            index += 1

            # Next term
            compile_term()

        wFile.write("</expression>\n")
 
    def compile_term():
        nonlocal index

        if index >= len(tokens):
            raise SyntaxError("Expected term")

        token = tokens[index]
        kind = token_type(token)

        wFile.write("<term>\n")

        # Integer constant
        if kind == "integerConstant":
            wFile.write(f"<integerConstant> {token} </integerConstant>\n")
            index += 1

        # String constant
        elif kind == "stringConstant":
            value = token[1:-1]  # Remove surrounding quotes
            value = (
                value.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )
            wFile.write(f"<stringConstant> {value} </stringConstant>\n")
            index += 1

        # Keyword constant
        elif token in {"true", "false", "null", "this"}:
            wFile.write(f"<keyword> {token} </keyword>\n")
            index += 1

        # Parenthesized expression
        elif token == "(":
            wFile.write("<symbol> ( </symbol>\n")
            index += 1

            compile_expression()

            if index < len(tokens) and tokens[index] == ")":
                wFile.write("<symbol> ) </symbol>\n")
                index += 1
            else:
                raise SyntaxError("Expected ')'")

        # Unary operation: -term or ~term
        elif token in {"-", "~"}:
            wFile.write(f"<symbol> {token} </symbol>\n")
            index += 1
            compile_term()

        # Identifier: variable, array access, or subroutine call
        elif kind == "identifier":
            wFile.write(f"<identifier> {token} </identifier>\n")
            index += 1

            # Array access: name[expression]
            if index < len(tokens) and tokens[index] == "[":
                wFile.write("<symbol> [ </symbol>\n")
                index += 1

                compile_expression()

                if index < len(tokens) and tokens[index] == "]":
                    wFile.write("<symbol> ] </symbol>\n")
                    index += 1
                else:
                    raise SyntaxError("Expected ']'")

            # Subroutine call: name(...) or object.name(...)
            elif index < len(tokens) and tokens[index] in {".", "("}:
                compile_subroutine_call()

        else:
            raise SyntaxError(f"Invalid term: {token}")

        wFile.write("</term>\n")
 
    def compile_subroutine_call():
        nonlocal index

        # The first identifier was already consumed by compile_term().
        # Check for a qualified call: objectOrClass.subroutineName(...)
        if index < len(tokens) and tokens[index] == ".":
            wFile.write("<symbol> . </symbol>\n")
            index += 1

            # Subroutine name
            if index < len(tokens) and token_type(tokens[index]) == "identifier":
                wFile.write(
                    f"<identifier> {tokens[index]} </identifier>\n"
                )
                index += 1
            else:
                raise SyntaxError("Expected subroutine name after '.'")

        # Opening parenthesis
        if index < len(tokens) and tokens[index] == "(":
            wFile.write("<symbol> ( </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected '(' in subroutine call")

        # Expression list
        compile_expression_list()

        # Closing parenthesis
        if index < len(tokens) and tokens[index] == ")":
            wFile.write("<symbol> ) </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ')' in subroutine call")

    def compile_expression_list():
        nonlocal index

        wFile.write("<expressionList>\n")

        # Empty list: foo()
        if index < len(tokens) and tokens[index] != ")":

            # First expression
            compile_expression()

            # Additional expressions separated by commas
            while index < len(tokens) and tokens[index] == ",":
                wFile.write("<symbol> , </symbol>\n")
                index += 1

                compile_expression()

        wFile.write("</expressionList>\n")

    def compile_parameter_list():
        nonlocal index

        wFile.write("<parameterList>\n")

        while index < len(tokens) and tokens[index] != ")":
            # Type
            if tokens[index] in {"int", "char", "boolean"}:
                wFile.write(
                    f"<keyword> {tokens[index]} </keyword>\n"
                )
                index += 1
            elif token_type(tokens[index]) == "identifier":
                wFile.write(
                    f"<identifier> {tokens[index]} </identifier>\n"
                )
                index += 1
            else:
                raise SyntaxError("Expected parameter type")

            # Parameter name
            if index < len(tokens) and token_type(tokens[index]) == "identifier":
                wFile.write(
                    f"<identifier> {tokens[index]} </identifier>\n"
                )
                index += 1
            else:
                raise SyntaxError("Expected parameter name")

            # Comma between parameters
            if index < len(tokens) and tokens[index] == ",":
                wFile.write("<symbol> , </symbol>\n")
                index += 1
            else:
                break

        wFile.write("</parameterList>\n")

    def compile_var_dec():
        nonlocal index

        wFile.write("<varDec>\n")

        # var
        if index < len(tokens) and tokens[index] == "var":
            wFile.write("<keyword> var </keyword>\n")
            index += 1
        else:
            raise SyntaxError("Expected 'var'")

        # Type
        if index < len(tokens) and tokens[index] in {
            "int", "char", "boolean"
        }:
            wFile.write(
                f"<keyword> {tokens[index]} </keyword>\n"
            )
            index += 1
        elif index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(
                f"<identifier> {tokens[index]} </identifier>\n"
            )
            index += 1
        else:
            raise SyntaxError("Expected variable type")

        # First variable name
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected variable name")

        # Additional names
        while index < len(tokens) and tokens[index] == ",":
            wFile.write("<symbol> , </symbol>\n")
            index += 1

            if index < len(tokens) and token_type(tokens[index]) == "identifier":
                wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
                index += 1
            else:
                raise SyntaxError("Expected variable name after ','")

        # Semicolon
        if index < len(tokens) and tokens[index] == ";":
            wFile.write("<symbol> ; </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ';' after var declaration")

        wFile.write("</varDec>\n")

    def compile_doStatement():
        nonlocal index

        wFile.write("<doStatement>\n")

        # do
        if index < len(tokens) and tokens[index] == "do":
            wFile.write("<keyword> do </keyword>\n")
            index += 1
        else:
            raise SyntaxError("Expected 'do'")

        # First identifier of the subroutine call
        if index < len(tokens) and token_type(tokens[index]) == "identifier":
            wFile.write(f"<identifier> {tokens[index]} </identifier>\n")
            index += 1
        else:
            raise SyntaxError("Expected subroutine name")

        # Parse the rest of the call
        compile_subroutine_call()

        # Semicolon
        if index < len(tokens) and tokens[index] == ";":
            wFile.write("<symbol> ; </symbol>\n")
            index += 1
        else:
            raise SyntaxError("Expected ';' after do statement")

        wFile.write("</doStatement>\n")

    def write_symbol(symbol):
        escaped = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            '"': "&quot;",
        }

        value = escaped.get(symbol, symbol)
        wFile.write(f"<symbol> {value} </symbol>\n")

    with open(output_file, "w") as wFile:
        wFile = IndentWriter(wFile)
        compile_class()


if __name__ == "__main__":
    JackAnalyzer()
