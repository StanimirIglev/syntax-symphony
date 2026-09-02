# TODO

## CI

- [ ] Add a pytest step with `PYTHONOPTIMIZE=1` (or `python -O`) to CI and the publish workflow, so validation cannot regress to `assert`-based checks that are stripped in optimized mode.

## Testing

Complementary techniques to add on top of the current fuzzer unit tests:

- [ ] **Property-based testing (Hypothesis)** — round-trip properties for `Grammar.to_dict()` / `normalize()`, `DT.to_dict()` → `DT.from_dict()`, and `is_nonterminal()` invariants; fuzzer invariants such as `remaining_k_paths()` never increasing.
- [ ] **Golden / snapshot tests** — with a fixed `seed`, compare fuzz output sequences for tiny grammars to catch unintended algorithm changes.
- [ ] **Mutation testing** — use a tool such as `mutmut` to measure and improve the strength of the fuzzer test suite.
