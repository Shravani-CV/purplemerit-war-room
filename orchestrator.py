"""
orchestrator.py - War Room Orchestrator / Coordinator
=====================================================
Manages the multi-agent workflow, collects reports from all agents,
synthesizes a final decision, and produces structured output.

Workflow:
  Phase 0: Initialize tools + agents
  Phase 1: DataAnalystAgent (MetricAnalyzer + AnomalyDetector)
  Phase 2: MarketingCommsAgent (SentimentAnalyzer)
  Phase 3: ProductManagerAgent (data + sentiment reports)
  Phase 4: SREAgent (infrastructure health)
  Phase 5: RiskCriticAgent (all reports)
  Phase 6: Orchestrator final decision synthesis
"""

import json
from datetime import datetime
from typing import Dict, Any, List

from tools import MetricAnalyzer, SentimentAnalyzer, AnomalyDetector
from agents import (DataAnalystAgent, ProductManagerAgent,
                    MarketingCommsAgent, RiskCriticAgent, SREAgent)


class WarRoomOrchestrator:
    """Central coordinator for the cross-functional war room."""

    def __init__(self, metrics_path, feedback_path, release_notes_path):
        self.start_time = datetime.now()
        self.trace_log = []

        self.log("=" * 70)
        self.log("PURPLEMERIT WAR ROOM - LAUNCH DECISION SYSTEM")
        self.log("=" * 70)
        self.log(f"Session started at {self.start_time.isoformat()}")
        self.log("")

        self.log("Loading release notes...")
        with open(release_notes_path, "r") as f:
            self.release_notes = json.load(f)
        self.log(f"  Feature: {self.release_notes['feature_name']} v{self.release_notes['version']}")
        self.log(f"  Known issues: {len(self.release_notes['known_issues'])}")

        self.log("")
        self.log("-" * 50)
        self.log("PHASE 0: INITIALIZING TOOLS")
        self.log("-" * 50)
        sc = self.release_notes.get("success_criteria", {})
        self.metric_analyzer = MetricAnalyzer(metrics_path, sc)
        self.sentiment_analyzer = SentimentAnalyzer(feedback_path)
        self.anomaly_detector = AnomalyDetector(metrics_path, z_threshold=2.0)

        self.log("")
        self.log("-" * 50)
        self.log("PHASE 0: INITIALIZING AGENTS")
        self.log("-" * 50)
        self.data_analyst = DataAnalystAgent(self.metric_analyzer, self.anomaly_detector)
        self.log(f"  [OK] {self.data_analyst.name} ready")
        self.pm_agent = ProductManagerAgent(self.release_notes)
        self.log(f"  [OK] {self.pm_agent.name} ready")
        self.comms_agent = MarketingCommsAgent(self.sentiment_analyzer)
        self.log(f"  [OK] {self.comms_agent.name} ready")
        self.risk_agent = RiskCriticAgent()
        self.log(f"  [OK] {self.risk_agent.name} ready")
        self.sre_agent = SREAgent(self.release_notes)
        self.log(f"  [OK] {self.sre_agent.name} ready")
        self.log("  Total agents: 5")
        self.log("")

    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [Orchestrator] {message}"
        self.trace_log.append(entry)
        print(entry)

    def run(self):
        # PHASE 1
        self.log("-" * 50)
        self.log("PHASE 1: DATA ANALYST AGENT")
        self.log("-" * 50)
        data_report = self.data_analyst.analyze()
        self.log(f"Phase 1 complete. Health: {data_report['synthesis']['health_score']}")
        self.log("")

        # PHASE 2
        self.log("-" * 50)
        self.log("PHASE 2: MARKETING/COMMS AGENT")
        self.log("-" * 50)
        sentiment_summary = self.sentiment_analyzer.get_sentiment_summary()
        comms_report = self.comms_agent.analyze({"recommendation": "PAUSE"})
        self.log(f"Phase 2 complete. Perception risk: {comms_report['perception_assessment']['risk_level']}")
        self.log("")

        # PHASE 3
        self.log("-" * 50)
        self.log("PHASE 3: PRODUCT MANAGER AGENT")
        self.log("-" * 50)
        pm_report = self.pm_agent.analyze(data_report, sentiment_summary)
        self.log(f"Phase 3 complete. PM recommendation: {pm_report['recommendation']}")
        self.log("")

        # PHASE 4
        self.log("-" * 50)
        self.log("PHASE 4: SRE AGENT")
        self.log("-" * 50)
        sre_report = self.sre_agent.analyze(data_report)
        self.log(f"Phase 4 complete. System status: {sre_report['system_status']}")
        self.log("")

        comms_report = self.comms_agent.analyze(pm_report)

        # PHASE 5
        self.log("-" * 50)
        self.log("PHASE 5: RISK/CRITIC AGENT")
        self.log("-" * 50)
        risk_report = self.risk_agent.analyze(data_report, pm_report, comms_report)
        self.log(f"Phase 5 complete. Risks: {risk_report['risk_summary']['total_risks']}, Score: {risk_report['risk_summary']['overall_risk_score']}")
        self.log("")

        # PHASE 6
        self.log("-" * 50)
        self.log("PHASE 6: ORCHESTRATOR - FINAL DECISION SYNTHESIS")
        self.log("-" * 50)
        final = self._synthesize(data_report, pm_report, comms_report, risk_report, sre_report)

        all_traces = (self.trace_log + self.data_analyst.get_trace() + self.pm_agent.get_trace() +
                      self.comms_agent.get_trace() + self.risk_agent.get_trace() + self.sre_agent.get_trace())
        final["_trace_log"] = all_traces

        self.log("")
        self.log("=" * 70)
        self.log(f"FINAL DECISION: {final['decision']}")
        self.log(f"CONFIDENCE: {final['confidence']['score']}%")
        self.log("=" * 70)
        return final

    def _synthesize(self, data_report, pm_report, comms_report, risk_report, sre_report):
        self.log("Collecting agent recommendations...")
        recs = {"DataAnalyst": data_report["synthesis"]["recommendation"],
                "ProductManager": pm_report["recommendation"],
                "RiskCritic": risk_report["recommendation"]}
        self.log(f"  Agent votes: {recs}")

        weights = {"DataAnalyst": 0.30, "ProductManager": 0.30, "RiskCritic": 0.25}
        scores = {"PROCEED": 0, "PAUSE": 0, "ROLL_BACK": 0}
        for agent, rec in recs.items():
            scores[rec] += weights.get(agent, 0.15)

        if sre_report["system_status"] == "DEGRADED":
            scores["ROLL_BACK"] += 0.15
            self.log("  SRE DEGRADED - adding weight to ROLL_BACK")
        elif sre_report["system_status"] == "WARNING":
            scores["PAUSE"] += 0.10

        decision = max(scores, key=scores.get)
        self.log(f"  Scores: {scores}")
        self.log(f"  Final decision: {decision}")

        synthesis = data_report["synthesis"]
        failing = synthesis.get("failing_criteria", {})
        sentiment_pct = comms_report.get("sentiment_analysis", {}).get("sentiment_percentages", {})
        top_themes = comms_report.get("perception_assessment", {}).get("top_complaint_themes", [])

        rationale = {"primary_drivers": [], "metric_references": {}, "feedback_summary": {}}
        for name, info in failing.items():
            rationale["primary_drivers"].append(f"{name} FAILING: actual={info['actual_value']} vs threshold={info['threshold']}")
            rationale["metric_references"][name] = info
        rationale["feedback_summary"] = {
            "total_feedback": comms_report.get("sentiment_analysis", {}).get("total_feedback", 0),
            "sentiment_distribution": sentiment_pct,
            "top_complaint_themes": [t["theme"] for t in top_themes],
            "urgent_feedback_count": comms_report.get("urgency_signals", {}).get("urgent_count", 0)
        }
        if decision == "PAUSE":
            rationale["primary_drivers"].insert(0, "Multiple success criteria failing with degrading trends, but feature adoption is positive and rollback may be premature.")
        elif decision == "ROLL_BACK":
            rationale["primary_drivers"].insert(0, "Critical stability and revenue metrics degrading. Immediate rollback recommended to prevent further user impact.")

        health = synthesis.get("health_score", 50)
        risk_score = risk_report["risk_summary"]["overall_risk_score"]
        confidence = min(95, health) if decision == "PROCEED" else min(95, (100 - health + risk_score) / 2 + 30)

        if decision == "ROLL_BACK":
            actions = [
                {"timeframe": "0-2 hours", "action": "Toggle feature flag smart_insights_enabled=false", "owner": "SRE Team", "priority": "P0"},
                {"timeframe": "0-2 hours", "action": "Rollback payment SDK to v3.7.x", "owner": "Payments Team", "priority": "P0"},
                {"timeframe": "0-4 hours", "action": "Deploy status page update and user communications", "owner": "Marketing/Comms", "priority": "P0"},
                {"timeframe": "2-6 hours", "action": "Root cause analysis for Android 13 crashes", "owner": "Mobile Engineering", "priority": "P1"},
                {"timeframe": "2-8 hours", "action": "Audit all payment transactions post-launch for failures/double-charges", "owner": "Finance + Payments", "priority": "P1"},
                {"timeframe": "4-12 hours", "action": "Prepare hotfix branch with crash fix + latency optimization", "owner": "Engineering Lead", "priority": "P1"},
                {"timeframe": "12-24 hours", "action": "Review and respond to all 1-star app store reviews", "owner": "Customer Success", "priority": "P2"},
                {"timeframe": "24-48 hours", "action": "Validate hotfix in staging environment", "owner": "QA Team", "priority": "P1"},
                {"timeframe": "24-48 hours", "action": "Prepare re-launch plan with gated rollout (10% -> 50% -> 100%)", "owner": "Product Manager", "priority": "P2"},
            ]
        elif decision == "PAUSE":
            actions = [
                {"timeframe": "0-2 hours", "action": "Halt rollout to new user segments", "owner": "Engineering Lead", "priority": "P0"},
                {"timeframe": "0-2 hours", "action": "Publish known issues acknowledgment on status page", "owner": "Marketing/Comms", "priority": "P0"},
                {"timeframe": "0-4 hours", "action": "Deploy hotfix for Android 13 crash (KI-001)", "owner": "Mobile Engineering", "priority": "P0"},
                {"timeframe": "2-6 hours", "action": "Investigate payment SDK timeout root cause", "owner": "Payments Team", "priority": "P1"},
                {"timeframe": "2-8 hours", "action": "Optimize database queries for latency reduction", "owner": "Backend Engineering", "priority": "P1"},
                {"timeframe": "4-12 hours", "action": "Scale support team and deploy auto-response", "owner": "Support Team Lead", "priority": "P1"},
                {"timeframe": "12-24 hours", "action": "Re-evaluate metrics after hotfix deployment", "owner": "Data Analyst", "priority": "P1"},
                {"timeframe": "24-48 hours", "action": "Decision checkpoint: proceed or rollback", "owner": "War Room (All)", "priority": "P0"},
            ]
        else:
            actions = [
                {"timeframe": "0-4 hours", "action": "Continue monitoring KPIs at 30-minute intervals", "owner": "Data Analyst", "priority": "P1"},
                {"timeframe": "0-4 hours", "action": "Address KI-001 as background fix", "owner": "Mobile Engineering", "priority": "P2"},
                {"timeframe": "4-12 hours", "action": "Expand rollout to next segment", "owner": "Product Manager", "priority": "P2"},
                {"timeframe": "12-24 hours", "action": "Launch marketing campaign", "owner": "Marketing/Comms", "priority": "P2"},
                {"timeframe": "24-48 hours", "action": "Full post-launch review", "owner": "All Teams", "priority": "P2"},
            ]

        return {
            "meta": {"system": "PurpleMerit War Room Decision System", "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "feature": self.release_notes["feature_name"],
                "feature_version": self.release_notes["version"],
                "agents_involved": ["DataAnalystAgent", "ProductManagerAgent", "MarketingCommsAgent", "RiskCriticAgent", "SREAgent"]},
            "decision": decision, "decision_scores": scores, "agent_recommendations": recs,
            "rationale": rationale, "risk_register": risk_report["risk_register"],
            "risk_summary": risk_report["risk_summary"],
            "assumption_challenges": risk_report["assumption_challenges"],
            "action_plan": {"timeframe": "24-48 hours", "actions": actions},
            "communication_plan": comms_report.get("communication_plan", {}),
            "confidence": {
                "score": round(confidence, 1),
                "factors": [f"Health score: {health}/100", f"Risk score: {risk_score}/100",
                    f"Failing criteria: {len(failing)}/{data_report['success_criteria_check']['_summary']['total_criteria']}",
                    f"Agent consensus: {len(set(recs.values()))} distinct recommendations"],
                "would_increase_confidence": [
                    "Device-specific crash rate breakdown (Android 13 segmentation)",
                    "A/B test data comparing feature-on vs feature-off cohorts",
                    "Payment failure correlation with specific payment methods",
                    "Real-time server logs for past 6 hours",
                    "User session replay data for crash scenarios"]
            },
            "detailed_reports": {
                "data_analyst": {"health_score": synthesis["health_score"],
                    "failing_criteria_count": synthesis["failing_criteria_count"],
                    "critical_anomaly_count": synthesis["critical_anomaly_count"],
                    "degrading_metrics": synthesis["degrading_metrics"],
                    "improving_metrics": synthesis["improving_metrics"]},
                "product_manager": {"user_impact": pm_report["user_impact_assessment"],
                    "feature_adoption": pm_report["feature_adoption"],
                    "go_nogo_framing": pm_report["go_nogo_framing"]},
                "marketing_comms": {"perception_risk": comms_report["perception_assessment"]["risk_level"],
                    "sentiment_percentages": sentiment_pct,
                    "urgent_feedback_count": comms_report["urgency_signals"]["urgent_count"]},
                "risk_critic": {"total_risks": risk_report["risk_summary"]["total_risks"],
                    "overall_risk_score": risk_report["risk_summary"]["overall_risk_score"],
                    "evidence_requested": risk_report["additional_evidence_requested"]},
                "sre": {"system_status": sre_report["system_status"],
                    "rollback_readiness": sre_report["rollback_readiness"]}
            }
        }
