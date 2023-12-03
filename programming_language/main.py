import sys
from lexer import Lexer
from parser import Parser
from evaluator import Evaluator

def run_habla(file_path):
    with open(file_path, 'r') as file:
        source_code = file.read()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    print("Tokens:", tokens)

    parser = Parser(tokens)
    ast = parser.parse()

    print("AST:", ast)

    evaluator = Evaluator(ast)
    evaluator.evaluate()

if __name__ == "__main__":
    file_path = sys.argv[1]  # El archivo .hb se pasa como argumento
    run_habla(file_path)
