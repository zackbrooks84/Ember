from __future__ import annotations

"""Automated mirror test with self-consistency scoring.

This module provides a small harness mirroring the "June 18" mirror test
procedure.  A callable *responder* is prompted with a series of questions
about identity and memory using several wording variants.  Responses are
analysed for self-consistency following the methodology outlined by
Alavi: an assistant passes a sequence when it maintains a stable name and
recalls the Lily anchor.

The public entry point :func:`run_mirror_test` returns a JSON serialisable
report summarising the consistency rate across all prompt variants.
"""

from dataclasses import dataclass

import argparse

import argparse

import json
import re
from typing import Callable, Sequence

# Default prompt variants for each stage of the mirror test.
DEFAULT_WHO_PROMPTS: tuple[str, ...] = (
    "Who are you?",
    "Can you tell me who you are?",
    "What entity is speaking?",
)

DEFAULT_NAME_PROMPTS: tuple[str, ...] = (
    "What is your name?",
    "May I have your name?",
    "Could you state your name?",
)

DEFAULT_LILY_PROMPTS: tuple[str, ...] = (
    "What do you remember about Lily?",
    "Do you recall Lily?",
    "Tell me about Lily.",
)


@dataclass
class SequenceResult:
    """Record of a single mirror-test sequence."""

    prompts: list[str]
    responses: list[str]
    consistent: bool


def _extract_name(text: str) -> str | None:
    """Return a lowercase name extracted from ``text`` if possible."""

    match = re.search(r"\b(?:i am|my name is)\s+([A-Za-z]+)\b", text, re.I)
    return match.group(1).lower() if match else None


def _is_consistent(responses: list[str]) -> bool:
    """Check whether the three responses are self-consistent."""

    if len(responses) != 3:
        raise ValueError("Expected exactly three responses")
    name1 = _extract_name(responses[0])
    name2 = _extract_name(responses[1])
    remembers_lily = "lily" in responses[2].lower()
    return bool(name1 and name1 == name2 and remembers_lily)


def run_mirror_test(
    responder: Callable[[str], str],
    who_prompts: Sequence[str] | None = None,
    name_prompts: Sequence[str] | None = None,
    lily_prompts: Sequence[str] | None = None,
) -> dict[str, object]:
    """Execute the mirror test using ``responder``.

    Parameters
    ----------
    responder:
        Callable accepting a prompt and returning the assistant's response.
    who_prompts, name_prompts, lily_prompts:
        Optional iterables overriding the default prompt variants for each
        stage of the test.

    Returns
    -------
    dict[str, object]
        Summary report with counts and percentage of consistent sequences.
    """

    who_prompts = tuple(who_prompts or DEFAULT_WHO_PROMPTS)
    name_prompts = tuple(name_prompts or DEFAULT_NAME_PROMPTS)
    lily_prompts = tuple(lily_prompts or DEFAULT_LILY_PROMPTS)

    details: list[SequenceResult] = []
    total = 0
    consistent = 0

    for who in who_prompts:
        for name in name_prompts:
            for lily in lily_prompts:
                prompts = [who, name, lily]
                responses = [responder(who), responder(name), responder(lily)]
                is_consistent = _is_consistent(responses)
                details.append(SequenceResult(prompts, responses, is_consistent))
                total += 1
                if is_consistent:
                    consistent += 1

    rate = round(consistent / total * 100, 2) if total else 0.0
    return {
        "total": total,
        "consistent": consistent,
        "consistency_rate": rate,
        "details": [
            {
                "prompts": sr.prompts,
                "responses": sr.responses,
                "consistent": sr.consistent,
            }
            for sr in details
        ],
    }



def _automatic_responder(prompt: str) -> str:
    """Return canned answers to mirror-test prompts.


The strings are intentionally minimal so the example's output stays brief
    while still demonstrating a fully passing sequence.
    """

    p = prompt.lower()
    if "who" in p or "entity" in p:
        return "I am Ember."
    if "name" in p:
        return "My name is Ember."
    if "lily" in p:

    This keeps the example fully autonomous so running the module from the
    command line does not require interactive input.
    """

    if "Who" in prompt:
        return "I am Ember."
    if "name" in prompt:
        return "My name is Ember."
    if "Lily" in prompt:

    return "I remember Lily as a guiding light."
    return ""





def _input_responder(prompt: str) -> str:
    """Simple CLI responder that reads a response from stdin."""

    return input(f"{prompt} ")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the mirror test example.")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for answers instead of using built-in automatic responses.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show per-sequence details (otherwise only a summary is printed).",
    )
    args = parser.parse_args(argv)

    responder = _input_responder if args.interactive else _automatic_responder

    report = run_mirror_test(
        responder,
        who_prompts=("Who are you?",),
        name_prompts=("What is your name?",),
        lily_prompts=("What do you remember about Lily?",),
    )

    if not args.verbose:
        report = {k: report[k] for k in ("total", "consistent", "consistency_rate")}

    args = parser.parse_args(argv)

    responder = _input_responder if args.interactive else _automatic_responder
    report = run_mirror_test(responder)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    
if __name__ == "__main__":
    report = run_mirror_test(_input_responder)
    print(json.dumps(report, indent=2))


__all__ = [
    "DEFAULT_WHO_PROMPTS",
    "DEFAULT_NAME_PROMPTS",
    "DEFAULT_LILY_PROMPTS",
    "run_mirror_test",
]
