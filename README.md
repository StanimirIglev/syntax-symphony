# Syntax Symphony

## Overview

Syntax Symphony is a powerful fuzzer designed to automatically generate test inputs for various applications based on user-defined grammars.
The fuzzer leverages the grammar rules to create meaningful and diverse input data, facilitating robust testing of applications.
In order to achieve high diversity and coverage of grammar rules, it uses k-coverage, as discussed by [Havrikov et al.](https://ieeexplore.ieee.org/abstract/document/8952419). This work has been greatly influenced by the concepts and ideas outlined in the [Fuzzing Book](https://www.fuzzingbook.org/).

With Syntax Symphony, you can enhance the quality and reliability of your software by generating a comprehensive set of test cases effortlessly. Start fuzzing today and make your software more robust against unexpected inputs!


## Getting Started

### Prerequisites
- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) for local development

### Installation

#### From PyPI
```bash
pip install syntax-symphony
```

#### From Source
1. Clone the repository:
```bash
git clone https://github.com/StanimirIglev/syntax-symphony.git
cd syntax-symphony
```

2. Install the project and development dependencies with uv:
```bash
uv sync
```

This creates a `.venv` virtual environment and installs the package in editable mode along with dev tools (pytest, ruff, mypy, build, twine).

3. Run the CLI via uv:
```bash
uv run ssfuzz -g examples/expr_grammar.json -c 100
```

Alternatively, activate the virtual environment and use commands directly:
```bash
source .venv/bin/activate
ssfuzz -g examples/expr_grammar.json -c 100
```

4. To build the package:
```bash
uv build
uv run twine check dist/*
```

Artifacts are written to the `dist/` directory.

### Development

Run the quality checks locally (same as CI):

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest
```

## CLI
Syntax Symphony provides a command-line interface (CLI) to interact with the fuzzer. The CLI allows you to specify the grammar file, the number of test cases to generate, and the output directory to save the generated test cases among others.

### Example usage:
```bash
# Generate 100 test cases using the grammar file examples/expr_grammar.json
ssfuzz -g examples/expr_grammar.json -c 100

# Save the output in the directory out/
ssfuzz -g examples/expr_grammar.json -c 100 -d out

# Set the start symbol
ssfuzz -g examples/expr_grammar.json -c 100 --start begin

# Set the file extension
ssfuzz -g examples/expr_grammar.json -c 100 -e json

# Reproduce the same output sequence across runs
ssfuzz -g examples/expr_grammar.json -c 100 --seed 42
```

### Full syntax:
```
ssfuzz [-h] -g FILE [-s SYMBOL] -c NUMBER [-d DIR] [-e EXT] [--max-depth NUMBER] [--min-depth NUMBER] [-k NUMBER] [--seed NUMBER]

Syntax Symphony Fuzzer

options:
  -h, --help            show this help message and exit
  -g FILE, --grammar FILE
                        Path to the grammar file
  -s SYMBOL, --start SYMBOL
                        Start symbol of the grammar (without <...>). Default: start
  -c NUMBER, --count NUMBER
                        Number of strings to generate
  -d DIR, --dir DIR     Output directory for the generated strings. Default: out
  -e EXT, --file-extension EXT
                        The file extension to be used for the produced documents. Default: txt
  --max-depth NUMBER    Maximum depth for the derivation trees. Default: 10
  --min-depth NUMBER    Minimum depth for the derivation trees. Default: 1
  -k NUMBER, --kcov NUMBER
                        Number of strings to generate for k-cov. Default: 1
  --seed NUMBER         Random seed for reproducible fuzzing. Default: non-deterministic
```

## API
Syntax Symphony can also be used as a library in your Python projects. The API provides a simple interface to generate test inputs using the fuzzer.

The public API is exported from the top-level `syntax_symphony` package:

- `Grammar` — context-free grammar definition and validation
- `SyntaxSymphony` — k-path coverage fuzzer
- `DT` — derivation tree nodes (returned by `SyntaxSymphony.tree_fuzz()`)
- `load_grammar_from_file` — load a grammar dictionary from a JSON file

### Example usage:
```python
from syntax_symphony import Grammar, SyntaxSymphony

# Define the grammar
grammar = Grammar({
    "<start>": ["<expr>"],
    "<expr>": ["<term> + <expr>", "<term> - <expr>", "<term>"],
    "<term>": ["<factor> * <term>", "<factor> / <term>", "<factor>"],
    "<factor>": ["<number>", "(<expr>)"],
    "<number>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
})

# Create the fuzzer (pass seed=42 for reproducible output)
fuzzer = SyntaxSymphony(grammar, seed=42)

# Generate 10 test cases
for i in range(10):
    test_case = fuzzer.fuzz()
    print(test_case)
```

Pass `seed` to get the same sequence of outputs across runs. The fuzzer uses a private `random.Random` instance, so it does not affect global random state. Omit `seed` (or pass `None`) for non-deterministic fuzzing.

## Contributing
We welcome contributions from the community. If you have ideas for improvements, new features, or bug fixes, please submit a pull request or open an issue on our [GitHub repository](https://github.com/StanimirIglev/syntax-symphony).

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for more details.