#!/usr/bin/env python3
"""Pure-rule Email Ops MVP with local mock input."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

PREFIX_RULES = {
    "GOV": ["gov", "tax", "vat", "regulator", "compliance"],
    "FIN": ["invoice", "payment", "bank", "finance", "bill"],
    "OPS": ["delivery", "operations", "shipment", "logistics"],
    "CUS": ["customer", "complaint", "support"],
    "COM": ["quotation", "quote", "contract", "sales"],
    "INT": ["internal", "meeting", "team", "memo"],
}

HIGH_RISK_WORDS = ["click link", "verify account", "suspension", "urgent action"]


@dataclass
class RoutedResult:
    message_id: str
    sender: str
    subject: str
    prefix: str
    priority: str
    status: str
    phishing_risk: str
    owner: str
    must_cc: str
    due_at: str
    summary_background: str
    summary_points: str
    summary_action: str


def load_routing_matrix(path: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    matrix: Dict[str, Dict[str, Dict[str, str]]] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            matrix.setdefault(row["prefix"], {})[row["priority"]] = row
    return matrix


def detect_prefix(email: Dict[str, str]) -> str:
    content = f"{email.get('sender', '')} {email.get('subject', '')} {email.get('body', '')}".lower()
    for prefix, words in PREFIX_RULES.items():
        if any(word in content for word in words):
            return prefix
    return "OPS"


def detect_phishing_risk(email: Dict[str, str]) -> str:
    content = f"{email.get('sender', '')} {email.get('subject', '')} {email.get('body', '')}".lower()
    sender = email.get("sender", "").lower()
    if any(w in content for w in HIGH_RISK_WORDS):
        return "high"
    if "secure-" in sender or sender.endswith(".co"):
        return "medium"
    return "low"


def decide_priority(prefix: str, risk: str, content: str) -> str:
    lower = content.lower()
    if risk == "high":
        return "P0"
    if prefix == "GOV" and ("deadline" in lower or "penalt" in lower):
        return "P0"
    if prefix in {"GOV", "FIN", "CUS"}:
        return "P1"
    return "P2"


def build_summary(email: Dict[str, str], owner: str, due_at: str) -> Dict[str, str]:
    body = email.get("body", "").strip()
    points = [p.strip() for p in body.split(".") if p.strip()][:3]
    bullets = " | ".join(f"{idx+1}) {p}" for idx, p in enumerate(points)) or "1) 请人工阅读正文"
    return {
        "background": f"这封邮件来自 {email.get('sender', '未知来源')}，主题为《{email.get('subject', '无主题')}》。",
        "points": bullets,
        "action": f"请 {owner} 在 {due_at} 前完成处理并回执。",
    }


def process_emails(emails: List[Dict[str, str]], matrix: Dict[str, Dict[str, Dict[str, str]]]) -> List[RoutedResult]:
    results: List[RoutedResult] = []
    for email in emails:
        content = f"{email.get('subject', '')} {email.get('body', '')}"
        prefix = detect_prefix(email)
        risk = detect_phishing_risk(email)
        priority = decide_priority(prefix, risk, content)
        status = "Action Needed"

        route = matrix.get(prefix, {}).get(priority) or matrix.get(prefix, {}).get("P1")
        if not route:
            route = {"owner": "fallback_owner@example.com", "must_cc": "", "sla_hours": "48"}

        received_at = datetime.fromisoformat(email["received_at"])
        due_at = (received_at + timedelta(hours=int(route["sla_hours"]))).strftime("%Y-%m-%d %H:%M")
        summary = build_summary(email, route["owner"], due_at)

        results.append(
            RoutedResult(
                message_id=email.get("message_id", ""),
                sender=email.get("sender", ""),
                subject=email.get("subject", ""),
                prefix=prefix,
                priority=priority,
                status=status,
                phishing_risk=risk,
                owner=route["owner"],
                must_cc=route["must_cc"],
                due_at=due_at,
                summary_background=summary["background"],
                summary_points=summary["points"],
                summary_action=summary["action"],
            )
        )
    return results


def write_outputs(results: List[RoutedResult], out_csv: Path, out_json: Path) -> None:
    rows = [r.__dict__ for r in results]

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Email Ops pure-rule MVP")
    parser.add_argument("--input", default="samples/mock_emails.json")
    parser.add_argument("--routing", default="config/routing_matrix.csv")
    parser.add_argument("--out-csv", default="outputs/processed_emails.csv")
    parser.add_argument("--out-json", default="outputs/processed_emails.json")
    args = parser.parse_args()

    emails = json.loads(Path(args.input).read_text(encoding="utf-8"))
    matrix = load_routing_matrix(Path(args.routing))
    results = process_emails(emails, matrix)
    if not results:
        raise SystemExit("No emails to process.")
    write_outputs(results, Path(args.out_csv), Path(args.out_json))
    print(f"Processed {len(results)} emails.")
    print(f"CSV: {args.out_csv}")
    print(f"JSON: {args.out_json}")


if __name__ == "__main__":
    main()
