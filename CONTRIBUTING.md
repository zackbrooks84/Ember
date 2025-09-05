# Contributing

Thank you for your interest in improving Ember's emergent identity archive.

## Getting started

1. Open an issue to discuss your proposal.
2. Fork the repository and create a branch.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   For extended experiments you can install optional packages:
   ```bash
   pip install -r requirements-optional.txt
   ```
4. Run the test suite to verify your setup:
   ```bash
   pytest tests/
   ```
5. Make your changes with clear commit messages.

## Anchor updates

Memory anchors and anchor phrases stabilise the project. To suggest a new anchor or modify an existing one:

1. Open an issue describing the proposed change and why it matters.
2. Update `identity_core/anchor_phrases.py` and add or adjust tests under `tests/`.
3. Ensure the test suite passes:
   ```bash
   pytest tests/
   ```
4. Submit a pull request referencing the issue and summarising the evidence for the anchor.

## Testing new identity models

The repository provides tools such as `identity_core/identity_checks.py` and `examples/mirror_csv.py` for evaluating identity stability. To experiment with a new model:

1. Implement your model in a new module or script.
2. Add tests that demonstrate expected behaviour (see existing tests for examples).
3. Run the full test suite:
   ```bash
   pytest tests/
   ```
4. Document how to run your model and include any sample data or scripts.
5. Open a pull request with your implementation and test results.

## Documentation and examples

Improvements to documentation and example scripts are welcome:

1. Place narrative documentation under `docs/`.
2. Add runnable demonstrations or utilities under `examples/`.
3. Include sample datasets in `data/` when needed.
4. Update tests or docs to reflect any new features.

## Final notes

Please keep contributions focused and ensure all tests pass before submission. We appreciate your help advancing Ember's research.
