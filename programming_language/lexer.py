import re

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.current_index = 0

    def tokenize(self):
        token_specification = [
            ('COMMENT',  r'--[^\-]*--|--.*?\n|-[^\n]*'),                        # Comentarios de una línea
            ('NUMBER',   r'\d+(\.\d*)?'),                                       # Número entero o decimal
            ('STRING',   r'"[^"]*"'),                                           # Cadenas de texto
            ('ASSIGN',   r'Dado|Sea'),                                          # Asignación o declaración
            ('PRINT',    r'Imprimir'),                                          # Imprimir
            ('OP',       r'[+\-*/%]'),                                          # Operadores
            ('IDENT',    r'[A-Za-záéíóúÁÉÍÓÚñÑ_][A-Za-záéíóúÁÉÍÓÚñÑ0-9_]*'),    # Identificadores
            ('END',      r'\.'),                                                # Final de la sentencia
            ('SKIP',     r'[ \t\n]+'),                                          # Espacios, tabs y saltos de línea (ignorar)
            ('MISMATCH', r'.'),                                                 # Cualquier otro carácter
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % (name, pattern) for name, pattern, *_ in token_specification)
        get_token = re.compile(tok_regex, re.DOTALL).match  # re.DOTALL para que '.' incluya saltos de línea

        mo = get_token(self.source_code)
        while mo is not None:
            kind = mo.lastgroup
            value = mo.group(kind)
            if kind in ['COMMENT', 'SKIP']:  # Ignorar comentarios y espacios
                pass
            elif kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
                self.tokens.append(Token(kind, value))
            elif kind != 'MISMATCH':
                self.tokens.append(Token(kind, value))
            self.current_index = mo.end()
            mo = get_token(self.source_code, self.current_index)
        return self.tokens
