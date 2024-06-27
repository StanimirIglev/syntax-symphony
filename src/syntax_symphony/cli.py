import argparse
import hashlib
import os
from .fuzzer import SyntaxSymphony
from .grammar import Grammar


def ssfuzz():
    parser = argparse.ArgumentParser(description="Syntax Symphony Fuzzer")
    parser.add_argument(
        "-g",
        "--grammar",
        dest="grammar",
        metavar="FILE",
        required=True,
        help="Path to the grammar file",
    )
    parser.add_argument(
        "-s",
        "--start",
        dest="start_symbol",
        default="start",
        metavar="SYMBOL",
        required=False,
        type=str,
        help="Start symbol of the grammar (without <...>). Default: start",
    )
    parser.add_argument(
        "-c",
        "--count",
        dest="count",
        metavar="NUMBER",
        required=True,
        type=int,
        help="Number of strings to generate",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="output_dir",
        metavar="DIR",
        default="out",
        required=False,
        type=str,
        help="Output directory for the generated strings. Default: out",
    )
    parser.add_argument(
        "-e",
        "--file-extension",
        dest="file_extension",
        metavar="EXT",
        default="txt",
        help="The file extension to be used for the produced documents. Default: txt",
    )
    parser.add_argument(
        "--max-depth",
        dest="max_depth",
        default=10,
        metavar="NUMBER",
        required=False,
        type=int,
        help="Maximum depth for the derivation trees. Default: 10",
    )
    parser.add_argument(
        "--min-depth",
        dest="min_depth",
        default=1,
        metavar="NUMBER",
        required=False,
        type=int,
        help="Minimum depth for the derivation trees. Default: 1",
    )
    parser.add_argument(
        "-k",
        "--kcov",
        dest="kcov",
        metavar="NUMBER",
        default=1,
        required=False,
        type=int,
        help="Number of strings to generate for k-cov. Default: 1",
    )

    args = parser.parse_args()

    with open(args.grammar, "r") as file:
        grammar_dict = eval(file.read())

    grammar = Grammar(grammar_dict, f"<{args.start_symbol}>")

    fuzzer = SyntaxSymphony(grammar, args.kcov, args.min_depth, args.max_depth)

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    for _ in range(args.count):
        string = fuzzer.fuzz()
        file_path = (
            f"{args.output_dir}/"
            + hashlib.sha256(
                string.encode(), usedforsecurity=False
            ).hexdigest()
            + f".{args.file_extension}"
        )
        with open(file_path, "w") as file:
            file.write(string)


if __name__ == "__main__":
    ssfuzz()
