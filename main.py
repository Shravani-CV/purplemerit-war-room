#!/usr/bin/env python3
"""
main.py - PurpleMerit War Room Launch Decision System
=====================================================
Entry point for the multi-agent war room simulation.

Usage:
    python main.py
    python main.py --metrics data/mock_metrics.csv --feedback data/user_feedback.json --release-notes data/release_notes.json
"""

import argparse
import json
import os
import sys
from datetime import datetime

from orchestrator import WarRoomOrchestrator


def main():
    parser = argparse.ArgumentParser(description="PurpleMerit War Room - Multi-Agent Launch Decision System")
    parser.add_argument("--metrics", default="data/mock_metrics.csv", help="Path to metrics CSV")
    parser.add_argument("--feedback", default="data/user_feedback.json", help="Path to user feedback JSON")
    parser.add_argument("--release-notes", default="data/release_notes.json", help="Path to release notes JSON")
    parser.add_argument("--output", default="output/war_room_decision.json", help="Path for output JSON")
    parser.add_argument("--trace-output", default="output/trace_log.txt", help="Path for trace log")
    args = parser.parse_args()

    for path, name in [(args.metrics, "Metrics"), (args.feedback, "Feedback"), (args.release_notes, "Release Notes")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} file not found: {path}")
            sys.exit(1)

    for p in [args.output, args.trace_output]:
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)

    print()
    print("*" * 70)
    print("*  PURPLEMERIT - CROSS-FUNCTIONAL WAR ROOM DECISION SYSTEM         *")
    print("*  Multi-Agent Launch Analysis                                      *")
    print("*" * 70)
    print()

    orchestrator = WarRoomOrchestrator(args.metrics, args.feedback, args.release_notes)
    result = orchestrator.run()
    trace_log = result.pop("_trace_log", [])

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n[OUTPUT] Decision JSON saved to: {args.output}")

    with open(args.trace_output, "w") as f:
        f.write("PURPLEMERIT WAR ROOM - EXECUTION TRACE LOG\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")
        for entry in trace_log:
            f.write(entry + "\n")
    print(f"[OUTPUT] Trace log saved to: {args.trace_output}")

    print("\n")
    print("=" * 70)
    print("                    WAR ROOM DECISION SUMMARY")
    print("=" * 70)
    print(f"  Feature:        {result['meta']['feature']} v{result['meta']['feature_version']}")
    print(f"  Decision:       >>> {result['decision']} <<<")
    print(f"  Confidence:     {result['confidence']['score']}%")
    print(f"  Risks:          {result['risk_summary']['total_risks']} identified")
    print(f"  Actions:        {len(result['action_plan']['actions'])} planned")
    print()
    print("  Agent Recommendations:")
    for agent, rec in result['agent_recommendations'].items():
        print(f"    - {agent:20s}: {rec}")
    print()
    print("  Key Rationale:")
    for driver in result['rationale']['primary_drivers'][:3]:
        print(f"    > {driver}")
    print()
    print("  Top Risks:")
    for risk in result['risk_register'][:3]:
        print(f"    [{risk['severity']:8s}] {risk['id']}: {risk['description'][:80]}...")
    print()
    print("=" * 70)
    print(f"  Full output: {args.output}")
    print(f"  Trace log:   {args.trace_output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
