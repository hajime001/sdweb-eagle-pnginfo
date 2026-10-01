"""Dependency-free matching for Eagle prompt-to-tag rules."""
import re


def saved_positive_prompt(info, fallback=""):
    if not isinstance(info, str) or not info.strip():
        return fallback if isinstance(fallback, str) else ""
    lines = []
    for line in info.splitlines():
        if line.startswith("Negative prompt:") or re.match(r"^Steps:\s*\d+\s*,", line):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def normalize(text, ignore_case=True):
    text = re.sub(r"\s+", " ", text.replace("_", " ")).strip()
    return text.casefold() if ignore_case else text


def prompt_tokens(prompt, ignore_case=True):
    result = set()
    for token in prompt.split(","):
        token = token.strip()
        # Remove standard SD emphasis wrappers and numeric weights.
        while len(token) > 1 and (token[0], token[-1]) in (("(", ")"), ("[", "]")):
            token = token[1:-1].strip()
            token = re.sub(r":\s*[-+]?\d+(?:\.\d+)?\s*$", "", token).strip()
        result.add(normalize(token, ignore_case))
    return result


def matching_tags(prompt, rules, mode="contains", ignore_case=True):
    if not isinstance(prompt, str) or not isinstance(rules, list):
        return []
    text = normalize(prompt, ignore_case)
    tokens = prompt_tokens(prompt, ignore_case)
    tags = []
    for row in rules:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            continue
        keyword, tag = row
        if not isinstance(keyword, str) or not isinstance(tag, str):
            continue
        keyword, tag = normalize(keyword, ignore_case), tag.strip()
        if not keyword or not tag:
            continue
        matches = keyword in tokens if mode == "token" else keyword in text
        if matches and tag not in tags:
            tags.append(tag)
    return tags
