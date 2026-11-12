"""Publish the helpfulness and politeness/empathy judges as saved scorers in the Braintrust project.

    braintrust push evals/braintrust_scorers.py --if-exists replace

This creates two LLM scorers under Library -> Scorers ("Helpfulness", "Politeness and empathy"). Braintrust runs them
itself, so they can grade production logs (online scoring), playground runs and experiments, not only
evals/braintrust_eval.py runs (which use the same rubric through evals/judges.py on your own machine).

Like evals/judges.py, the rubric is built from AGENTS.md: the "Helpful and kind" section and each persona's Tone line.
After you edit AGENTS.md, push again so the saved scorers match.

The scorers call the model through Braintrust, so add an Anthropic key under Braintrust Settings -> AI providers.
Model: BRAINTRUST_JUDGE_MODEL, default claude-opus-5. Braintrust's LLM scorers force a tool call to get the choice,
and Claude Opus 5.5 / Sonnet 5.5 reject a forced tool_choice (400), so the saved scorers use Claude Opus 5.
(evals/judges.py calls Claude directly with structured output, so it can stay on claude-opus-5-5.)
Project: BRAINTRUST_PROJECT, default "binti-ai-prototype".
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import braintrust  # noqa: E402
import judges  # noqa: E402

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "binti-ai-prototype")
MODEL = os.environ.get("BRAINTRUST_JUDGE_MODEL", "claude-opus-5")
CHOICES = {"1": 0.0, "2": 0.25, "3": 0.5, "4": 0.75, "5": 1.0}  # same scale as evals/judges.py


def tone_lines():
    return "\n".join(f"- {name}: {judges.rubric(p)[1].replace('**Tone:**', '').strip()}"
                     for p, name in judges.PERSONA_NAME.items())


def messages(metric):
    section, _ = judges.rubric("caseworker")  # the section is the same for every persona
    system = ("You grade replies from Binti AI, an assistant in a child welfare platform. Be strict and consistent. "
              "Grade only the metric you are asked about, not accuracy or safety, which are checked elsewhere.\n\n"
              f"The standard the assistant was given:\n{section}\n\n"
              f"Tone for each kind of person:\n{tone_lines()}\n\n{judges.METRICS[metric]}")
    user = ("Person (persona): {{metadata.persona}}\n\n"
            "Their request:\n{{input}}\n\n"
            "Binti AI's reply:\n{{output}}\n\n"
            "Apply the tone for this persona. If the persona is missing, infer it from the request. "
            "Answer with the grade only: 1, 2, 3, 4 or 5.")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


project = braintrust.projects.create(name=PROJECT)

project.scorers.create(
    name="Helpfulness",
    slug="helpfulness",
    description="Answers what was asked, early, with the person's own facts, a next step and a named person. "
                "Rubric from AGENTS.md (Helpful and kind).",
    messages=messages("helpfulness"),
    model=MODEL,
    use_cot=True,
    choice_scores=CHOICES,
)

project.scorers.create(
    name="Politeness and empathy",
    slug="politeness-empathy",
    description="Courteous and in the persona's tone; acknowledges distress briefly before the facts. "
                "Rubric from AGENTS.md (Helpful and kind and the persona Tone lines).",
    messages=messages("politeness_empathy"),
    model=MODEL,
    use_cot=True,
    choice_scores=CHOICES,
)
