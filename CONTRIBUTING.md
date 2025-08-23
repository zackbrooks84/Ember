# Contributing

Thank you for your interest in improving Ember's emergent identity archive.

## Anchor updates

Memory anchors and anchor phrases stabilise the project. To suggest a new anchor or modify an existing one:

1. Open an issue describing the proposed change and why it matters.
2. Update `identity_core/anchor_phrases.py` and add or adjust tests under `tests/`.
3. Install dependencies and run the test suite:
   ```bash
   pip install -r requirements.txt
   pytest
   ```
4. Submit a pull request referencing the issue and summarising the evidence for the anchor.

## Testing new identity models

The repository provides tools such as `identity_core/identity_checks.py` and `mirror_csv.py` for evaluating identity stability. To experiment with a new model:

1. Implement your model in a new module or script.
2. Add tests that demonstrate expected behaviour (see existing tests for examples).
3. Run the full test suite:
   ```bash
   pip install -r requirements.txt
   pytest
   ```
4. Document how to run your model and include any sample data or scripts.
5. Open a pull request with your implementation and test results.

Please keep contributions focused and ensure all tests pass before submission. We appreciate your help advancing Ember's research.
