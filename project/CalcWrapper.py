import subprocess, re, pathlib, os

operators = {"(": -1, "=": 0, "+" : 1, "-" : 1, "*" : 2, "/" : 2, "^": 3, "log" : 3}

# executes a racket program given the program's file path and arguments, and returns the part of the output captured by the regex
def exec_racket_prog(file_path, arg, extract_regex):
    out = str(subprocess.run(['racket', file_path, arg],
            stdout=subprocess.PIPE).stdout)    
    return(re.search(extract_regex, out).group(1))

# returns the absolute filePath of a relative path beginning from the current directory (/project)
def rel_to_abs_path(relative_path): 
    return(os.path.join(pathlib.Path(__file__).parent.absolute(),relative_path))

# returns the a list of constraints that make up the constraint system given a prefixed, parenthesized equation
def build_constraint_list(converted_eqn):
    return(exec_racket_prog(rel_to_abs_path("racket/ConstraintListBuilder.rkt"), converted_eqn, "\'(.*)\\\\n"))

# returns the full Racket-executable constraint system
def build_constraint_system(constraint_network):
    return(exec_racket_prog(rel_to_abs_path("racket/ConstraintSystemBuilder.rkt"), constraint_network, "\"(.*)\""))

# convert rational numbers into floating point numbers
def convert(s):
    try:
        return float(s)
    except ValueError:
        num, denom = s.split('/')
        return float(num) / float(denom)

# returns the value of the unknown in the constraint system
def exec_constraint_system(constraint_system):
    file_path = rel_to_abs_path("racket/TempConstraintSystem.rkt")
    con_sys_file = open(file_path, 'w')
    con_sys_file.write("#lang racket\n(require \"ConstraintSystemBase.rkt\")\n" + constraint_system)
    con_sys_file.close()
    return(exec_racket_prog(file_path, constraint_system, "'(.*)\\\\n'"))

def replace_with_spaces(replace, string):
    for i in replace:
        string = string.replace(i, " " + i +" ")
    return string

def unary_to_binary_minus(charList):
    for i, c in enumerate(charList):
        if i == len(charList) - 1:
            continue
        elif c == "-" and (i == 0 or charList[i-1] in operators.keys()):
            charList.insert(i,"(")
            charList[i+1]="-1"
            charList.insert(i+2,"*")
            operandEndIndex = i+4
            if charList[i+3] in operators.keys():
                for c in charList[i+4:]:
                    operandEndIndex += 1
                    if c == ")":
                        break;
            charList.insert(operandEndIndex,")")
    return charList

def tokenize(eq):
    operators_and_paren = list(operators.keys())
    operators_and_paren.append(")")
    eq = replace_with_spaces(operators_and_paren, eq)
    return eq.split()

def rev(eq):
    rev_eq = []
    for i in eq[::-1]:
        if i == "(":
            rev_eq.append(")")
        elif i == ")":
            rev_eq.append("(")
        else:
            rev_eq.append(i)

    return rev_eq

def is_number(s):
    return s.isnumeric() or s[1:].isnumeric()

def in_to_pre(raw_eq):
    formula = rev(unary_to_binary_minus(tokenize(raw_eq)))

    op_stack = []
    eq = []

    for token in formula:
        if (token == "("):
            op_stack.append("(")
        elif (token == ")"):
            while(op_stack[-1] != "("):
                eq.append(op_stack.pop())
            op_stack.pop()
        elif token in operators.keys():
            if (len(op_stack) == 0 or operators[token] > operators[op_stack[-1]]):
                op_stack.append(token)
            else:
                while (len(op_stack) != 0 and operators[token] <= operators[op_stack[-1]]):
                    eq.append(op_stack.pop())
                op_stack.append(token)
        elif token.isalpha() or is_number(token):
            eq.append(token)

    while op_stack:
        eq.append(op_stack.pop())

    return rev(eq)

def parenthesize(formula):
    operator_amounts = {"=" : 2, "+" : 2, "-" : 2, "*" : 2, "/" : 2, "^": 2}

    eq = ""
    op_stack, operands = [], []
    occurences = [0]

    for char in formula:
        while op_stack and operator_amounts[op_stack[-1]] == occurences[-1]:
            eq = eq[:-1]
            eq += ") "
            occurences.pop()
            occurences[-1] += 1
            op_stack.pop()

        if char in operator_amounts.keys():
            eq += "(" + char + " "
            op_stack.append(char)
            occurences.append(0)
        elif char.isalpha() or is_number(char):
            eq += "(" + char + ")"  + " "
            occurences[-1] += 1


    while eq[-1] == " ":
        eq = eq[:-1]
    for i in op_stack:
        eq += ")"

    return eq

def convert_to_scheme(raw_eq):
    return(parenthesize(in_to_pre(raw_eq)))
