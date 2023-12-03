from parser import ASTNode, VariableDeclaration, VariableAssignment, PrintCommand, MathOperation

class Evaluator:
    def __init__(self, ast):
        self.ast = ast
        self.environment = {}

    def evaluate(self):
        for node in self.ast:
            if isinstance(node, VariableDeclaration):
                self.handle_declaration(node)
            elif isinstance(node, VariableAssignment):
                self.handle_assignment(node)
            elif isinstance(node, PrintCommand):
                self.handle_print(node)

    def handle_declaration(self, node):
        # Simplemente registra la variable en el entorno con un valor nulo o predeterminado
        self.environment[node.var_name] = 0

    def handle_assignment(self, node):
        # Asigna el valor a la variable en el entorno
        self.environment[node.var_name] = node.value

    def handle_print(self, node):
        if isinstance(node.content, MathOperation):
            result = self.evaluate_math_operation(node.content)
            print(result)
        elif isinstance(node.content, str):
            # Si el contenido es una cadena, puede ser una variable o una cadena literal
            if node.content in self.environment:
                # Si la cadena es una variable en el entorno, imprimir su valor
                print(self.environment[node.content])
            else:
                # Si no, imprimir la cadena literal
                print(node.content)

    def evaluate_math_operation(self, math_op):
        # Evaluar la operación matemática
        left_operand = self.evaluate_operand(math_op.left_operand)
        right_operand = self.evaluate_operand(math_op.right_operand)

        if math_op.operator == '+':
            return left_operand + right_operand
        elif math_op.operator == '-':
            return left_operand - right_operand
        elif math_op.operator == '*':
            return left_operand * right_operand
        elif math_op.operator == '/':
            # Agregar una comprobación para evitar la división por cero
            return left_operand / right_operand if right_operand != 0 else None
        elif math_op.operator == '%':
            # Módulo (resto de la división)
            return left_operand % right_operand
        else:
            # Operador no reconocido o no soportado
            return None

    def evaluate_operand(self, operand):
        # Convertir el operando a un número si es posible, de lo contrario buscar en el entorno
        if isinstance(operand, (int, float)):
            return operand
        elif isinstance(operand, str) and operand in self.environment:
            return self.environment[operand]
        else:
            # Manejo de error o valor por defecto
            return 0
