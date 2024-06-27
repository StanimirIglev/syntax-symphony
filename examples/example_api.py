from syntax_symphony.fuzzer import SyntaxSymphony
from syntax_symphony.grammar import Grammar

# Define the grammar
grammar = Grammar(
    {
        "<start>": ["<expr>"],
        "<expr>": ["<term> + <expr>", "<term> - <expr>", "<term>"],
        "<term>": ["<factor> * <term>", "<factor> / <term>", "<factor>"],
        "<factor>": ["<number>", "(<expr>)"],
        "<number>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    }
)

# Create the fuzzer
fuzzer = SyntaxSymphony(grammar)

# Generate 10 test cases
for i in range(10):
    test_case = fuzzer.fuzz()
    print(test_case)
