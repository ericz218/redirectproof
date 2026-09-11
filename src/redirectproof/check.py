from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    source: str
    destination: str
    status: int
    location: str


@dataclass(frozen=True)
class Finding:
    rule: str
    message: str
    location: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _netlify(path: Path) -> tuple[list[Rule], list[Finding]]:
    rules: list[Rule] = []
    findings: list[Finding] = []
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        location = f"{path}:{number}"
        if len(parts) < 2:
            findings.append(Finding("RP001", "Invalid _redirects rule", location))
            continue
        try:
            status = int(parts[2].rstrip("!")) if len(parts) >= 3 else 301
        except ValueError:
            findings.append(Finding("RP002", "Invalid redirect status", location))
            continue
        rules.append(Rule(parts[0], parts[1], status, location))
    return rules, findings


def _vercel(path: Path) -> tuple[list[Rule], list[Finding]]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [], [Finding("RP001", f"Invalid vercel.json: {exc}", str(path))]
    rules: list[Rule] = []
    findings: list[Finding] = []
    for index, item in enumerate(data.get("redirects", [])):
        location = f"{path}:redirects[{index}]"
        if not isinstance(item, dict) or not isinstance(item.get("source"), str) or not isinstance(item.get("destination"), str):
            findings.append(Finding("RP001", "Redirect requires string source and destination", location))
            continue
        status = item.get("statusCode", 308 if item.get("permanent", False) else 307)
        if not isinstance(status, int):
            findings.append(Finding("RP002", "Invalid redirect status", location))
            continue
        rules.append(Rule(item["source"], item["destination"], status, location))
    return rules, findings


def _is_concrete(path: str) -> bool:
    return not any(char in path for char in "*:(){}")


def _analyze(rules: list[Rule]) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, Rule] = {}
    graph: dict[str, str] = {}
    catch_all_seen = False
    for item in rules:
        if item.status not in {200, 301, 302, 303, 307, 308, 404}:
            findings.append(Finding("RP101", f"Unsupported redirect or rewrite status {item.status}", item.location))
        is_redirect = 300 <= item.status < 400
        if is_redirect and item.source == item.destination:
            findings.append(Finding("RP102", "Redirect points to itself", item.location))
        if item.source in seen:
            findings.append(Finding("RP103", f"Duplicate source; first declared at {seen[item.source].location}", item.location))
        else:
            seen[item.source] = item
        if catch_all_seen:
            findings.append(Finding("RP104", "Rule is shadowed by an earlier catch-all", item.location))
        if item.source in ("/*", "/:path*", "/(.*)"):
            catch_all_seen = True
        if is_redirect and _is_concrete(item.source) and _is_concrete(item.destination) and item.destination.startswith("/"):
            graph[item.source] = item.destination

    for source, first in graph.items():
        visited = {source}
        current = first
        while current in graph:
            if current in visited:
                findings.append(Finding("RP105", f"Redirect cycle includes {current}", seen[source].location))
                break
            visited.add(current)
            current = graph[current]
    unique = {(item.rule, item.location): item for item in findings}
    return list(unique.values())


def check(path: Path) -> list[Finding]:
    files: list[Path]
    if path.is_dir():
        files = [candidate for candidate in (path / "_redirects", path / "public" / "_redirects", path / "vercel.json") if candidate.is_file()]
    else:
        files = [path]
    if not files:
        return [Finding("RP000", "No _redirects or vercel.json found", str(path))]

    rules: list[Rule] = []
    findings: list[Finding] = []
    for file in files:
        parsed, errors = _vercel(file) if file.name == "vercel.json" else _netlify(file)
        rules.extend(parsed)
        findings.extend(errors)
    findings.extend(_analyze(rules))
    return findings
