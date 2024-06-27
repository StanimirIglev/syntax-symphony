# Syntax Symphony

## Overview

Syntax Symphony is a powerful fuzzer designed to automatically generate test inputs for various applications based on user-defined grammars.
The fuzzer leverages the grammar rules to create meaningful and diverse input data, facilitating robust testing of applications.
In order to achieve high diversity and coverage of grammar rules, it uses k-coverage, as discussed by [Havrikov et al.](https://ieeexplore.ieee.org/abstract/document/8952419). This work has been greatly influenced by the concepts and ideas outlined in the [Fuzzing Book](https://www.fuzzingbook.org/).

With Syntax Symphony, you can enhance the quality and reliability of your software by generating a comprehensive set of test cases effortlessly. Start fuzzing today and make your software more robust against unexpected inputs!


## Getting Started

### Prerequisites
- Python 3.10 or higher

### Installation

#### From PyPI
```bash
pip install syntax-symphony
```
#### From Source
1. Clone the repository:
```bash
git clone
cd syntax_symphony
```

2. We recommend creating a virtual environment to install the dependencies:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

3. Install locally (add flag -e to install in editable mode):
```bash
pip install .
```

4. To build the package:
```bash
python -m pip install build
python -m build
```
This should create the package in the `dist/` directory.

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
```

### Full syntax:
```
ssfuzz [-h] -g FILE [-s SYMBOL] -c NUMBER [-d DIR] [-e EXT] [--max-depth NUMBER] [--min-depth NUMBER] [-k NUMBER]

Syntax Symphony Fuzzer

options:
  -h, --help            show this help message and exit
  -g FILE, --grammar FILE
                        Path to the grammar file
  -s SYMBOL, --start SYMBOL
                        Start symbol of the grammar (without <...>). Default: start
  -c NUMBER, --count NUMBER
                        Number of strings to generate
  -d DIR, --dir DIR     Output directory for the generated strings. Default: output
  -e EXT, --file-extension EXT
                        The file extension to be used for the produced documents. Default: txt
  --max-depth NUMBER    Maximum depth for the derivation trees. Default: 10
  --min-depth NUMBER    Minimum depth for the derivation trees. Default: 1
  -k NUMBER, --kcov NUMBER
                        Number of strings to generate for k-cov. Default: 1
```

## API
Syntax Symphony can also be used as a library in your Python projects. The API provides a simple interface to generate test inputs using the fuzzer.

### Example usage:
```python
from syntax_symphony.fuzzer import SyntaxSymphony
from syntax_symphony.grammar import Grammar

# Define the grammar
grammar = Grammar({
    "<start>": ["<expr>"],
    "<expr>": ["<term> + <expr>", "<term> - <expr>", "<term>"],
    "<term>": ["<factor> * <term>", "<factor> / <term>", "<factor>"],
    "<factor>": ["<number>", "(<expr>)"],
    "<number>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
})

# Create the fuzzer
fuzzer = SyntaxSymphony(grammar)

# Generate 10 test cases
for i in range(10):
    test_case = fuzzer.fuzz()
    print(test_case)
```

## Contributing
We welcome contributions from the community. If you have ideas for improvements, new features, or bug fixes, please submit a pull request or open an issue on our GitHub repository.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for more details.