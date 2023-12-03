from lexer import Lexer, Token

class ASTNode:
    pass

class VariableDeclaration(ASTNode):
    def __init__(self, var_name):
        self.var_name = var_name

    def __repr__(self):
        return f"VariableDeclaration(var_name={self.var_name})"

class VariableAssignment(ASTNode):
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

    def __repr__(self):
        return f"VariableAssignment(var_name={self.var_name}, value={self.value})"

class MathOperation(ASTNode):
    def __init__(self, operator, left_operand, right_operand):
        self.operator = operator
        self.left_operand = left_operand
        self.right_operand = right_operand

    def __repr__(self):
        return f"MathOperation({self.operator}, {self.left_operand}, {self.right_operand})"

class PrintCommand(ASTNode):
    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return f"PrintCommand(content={self.content})"

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_index = 0
        self.ast = []

    def parse(self):
        while self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            if token.type == 'ASSIGN':
                self.parse_assignment_or_declaration()
            elif token.type == 'PRINT':
                self.parse_print()
            else:
                self.current_index += 1
        return self.ast

    def parse_assignment_or_declaration(self):
        assign_token = self.next_token()
        var_name_token = self.next_token()
        value = None

        # Si el siguiente token es 'igual', entonces es una asignación
        if self.peek_token().type == 'IDENT' and self.peek_token().value == 'igual':
            self.next_token()  # Consumir 'igual'
            if self.peek_token().type == 'IDENT' and self.peek_token().value == 'a':
                self.next_token()  # Consumir 'a'
                value_token = self.next_token()
                if value_token.type in ['NUMBER', 'IDENT', 'STRING']:
                    value = value_token.value
                    if value_token.type == 'STRING':
                        value = value.strip('"')

        if value is None:
            self.ast.append(VariableDeclaration(var_name_token.value))
        else:
            self.ast.append(VariableAssignment(var_name_token.value, value))

        self.next_token()  # Consumir el token de fin de sentencia

    def parse_math_operation(self):
        left_operand = self.next_token()
        operator = self.next_token()
        right_operand = self.next_token()

        if operator.type == 'OP' and left_operand.type in ['NUMBER', 'IDENT'] and right_operand.type in ['NUMBER', 'IDENT']:
            return MathOperation(operator.value, left_operand.value, right_operand.value)
        else:
            # Manejo de error o casos no soportados
            return None

    def parse_print(self):
        self.next_token()  # Consumir 'Imprimir'

        if self.check_next_tokens(['el', 'resultado', 'de', 'la']):
            # Este es un caso especial para operaciones matemáticas en lenguaje natural
            # Consumir 'el', 'resultado', 'de', 'la'
            for _ in range(4): self.next_token()
            math_operation = self.parse_natural_language_math_operation()
            self.ast.append(PrintCommand(math_operation))
        elif self.peek_token().type == 'IDENT':
            if self.check_next_tokens(['el', 'contenido', 'de']):
                # Consumir 'el', 'contenido', 'de'
                for _ in range(3): self.next_token()
                variable_token = self.next_token()
                self.ast.append(PrintCommand(variable_token.value))
            else:
                content = self.next_token().value
                self.ast.append(PrintCommand(content))
        else:
            # Otros casos para imprimir
            pass
        
        self.next_token()  # Consumir el token de fin de sentencia

    def check_next_tokens(self, token_values):
        # Verifica si los próximos tokens coinciden con una lista dada de valores
        for i, value in enumerate(token_values):
            if not (self.current_index + i < len(self.tokens) and self.tokens[self.current_index + i].value == value):
                return False
        return True

    def parse_natural_language_math_operation(self):
        # Consumir tokens hasta llegar a la operación matemática
        while self.peek_token().value not in ['suma', 'resta', 'multiplicación', 'división', 'módulo']:
            self.next_token()
        
        operator = self.next_token()  # Este es el token de la operación (suma, resta, etc.)
        self.next_token()  # Consumir 'de'
        left_operand = self.next_token()  # Primer operando
        self.next_token()  # Consumir 'y'
        right_operand = self.next_token()  # Segundo operando

        # Asignar el operador matemático correcto
        if operator.value == 'suma':
            op_symbol = '+'
        elif operator.value == 'resta':
            op_symbol = '-'
        elif operator.value == 'multiplicación':
            op_symbol = '*'
        elif operator.value == 'división':
            op_symbol = '/'
        elif operator.value == 'módulo':
            op_symbol = '%'
        # Aquí podrías añadir más operaciones

        return MathOperation(op_symbol, left_operand.value, right_operand.value)

    def next_token(self):
        token = self.tokens[self.current_index]
        self.current_index += 1
        return token

    def peek_token(self):
        return self.tokens[self.current_index]
