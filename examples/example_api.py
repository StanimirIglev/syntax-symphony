from syntax_symphony import Grammar, SyntaxSymphony

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
for _ in range(10):
    test_case = fuzzer.fuzz()
    print(test_case)  # noqa: T201
