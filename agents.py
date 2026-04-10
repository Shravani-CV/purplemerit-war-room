"""
agents.py - War Room Agent Definitions
=======================================
Each agent has clear responsibility, calls tools programmatically,
and returns typed dictionaries.
"""

import json
from typing import Dict, Any, List
from datetime import datetime


class BaseAgent:
    """Base class for all war room agents."""
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.trace_log: List[str] = []

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = f"[{timestamp}] [{self.name}] {message}"
        self.trace_log.append(entry)
        print(entry)

    def get_trace(self) -> List[str]:
        return self.trace_log


class DataAnalystAgent(BaseAgent):
    """Analyses quantitative metrics, trends, anomalies, and confidence."""

    def __init__(self, metric_analyzer, anomaly_detector):
        super().__init__("DataAnalystAgent", "Data Analyst")
        self.metric_analyzer = metric_analyzer
        self.anomaly_detector = anomaly_detector

    def analyze(self) -> Dict[str, Any]:
        self.log("Starting quantitative analysis...")
        self.log("Invoking MetricAnalyzer.get_summary_statistics()")
        summary = self.metric_analyzer.get_summary_statistics()
        self.log("Invoking MetricAnalyzer.check_success_criteria()")
        criteria = self.metric_analyzer.check_success_criteria()
        self.log("Invoking MetricAnalyzer.get_trend_analysis()")
        trends = self.metric_analyzer.get_trend_analysis()
        self.log("Invoking AnomalyDetector.detect_anomalies()")
        anomalies = self.anomaly_detector.detect_anomalies()

        failing_criteria = {k: v for k, v in criteria.items()
                          if k != "_summary" and v.get("status") == "FAIL"}
        critical_anomalies = []
        for metric, info in anomalies.get("anomalies_by_metric", {}).items():
            for a in info["anomalies"]:
                if a["severity"] == "critical":
                    critical_anomalies.append({"metric": metric, **a})

        pass_rate = criteria["_summary"]["pass_rate_pct"]
        anomaly_penalty = min(anomalies["total_anomalies_detected"] * 3, 30)
        health_score = max(0, pass_rate - anomaly_penalty)

        degrading, improving = [], []
        bad_if_up = ["crash_rate_pct", "api_latency_p95_ms", "support_ticket_volume", "churn_rate_pct"]
        for col, info in summary.items():
            direction = info.get("trend")
            if col in bad_if_up:
                if direction == "increasing": degrading.append(col)
                elif direction == "decreasing": improving.append(col)
            else:
                if direction == "decreasing": degrading.append(col)
                elif direction == "increasing": improving.append(col)

        rec = "ROLL_BACK" if (health_score < 30 or len(critical_anomalies) >= 3 or len(failing_criteria) >= 5) else               "PAUSE" if (health_score < 60 or len(critical_anomalies) >= 1 or len(failing_criteria) >= 3) else "PROCEED"

        self.log(f"Analysis complete. Health: {health_score}/100, Failing: {len(failing_criteria)}, Anomalies: {len(critical_anomalies)}")
        return {
            "agent": self.name, "summary_statistics": summary,
            "success_criteria_check": criteria, "trend_analysis": trends,
            "anomaly_report": anomalies,
            "synthesis": {
                "health_score": round(health_score, 1),
                "failing_criteria": failing_criteria,
                "failing_criteria_count": len(failing_criteria),
                "critical_anomalies": critical_anomalies,
                "critical_anomaly_count": len(critical_anomalies),
                "degrading_metrics": degrading,
                "improving_metrics": improving,
                "recommendation": rec
            }
        }


class ProductManagerAgent(BaseAgent):
    """Defines success criteria, user impact, and go/no-go framing."""

    def __init__(self, release_notes: Dict):
        super().__init__("ProductManagerAgent", "Product Manager")
        self.release_notes = release_notes

    def analyze(self, data_analyst_report: Dict, sentiment_report: Dict) -> Dict[str, Any]:
        self.log("Evaluating launch success criteria and user impact...")
        criteria_check = data_analyst_report["success_criteria_check"]
        synthesis = data_analyst_report["synthesis"]
        known_issues = self.release_notes.get("known_issues", [])

        self.log("Cross-referencing known issues with observed metrics...")
        ki_matches = []
        for ki in known_issues:
            ki_desc = ki["description"].lower()
            matched = False
            if "crash" in ki_desc and "crash_rate_pct" in synthesis.get("degrading_metrics", []):
                matched = True
            if "payment" in ki_desc and "payment_success_rate_pct" in synthesis.get("degrading_metrics", []):
                matched = True
            if "latency" in ki_desc and "api_latency_p95_ms" in synthesis.get("degrading_metrics", []):
                matched = True
            ki_matches.append({"issue_id": ki["id"], "severity": ki["severity"],
                "description": ki["description"], "observed_in_metrics": matched,
                "eta_fix": ki.get("eta_fix", "Unknown")})

        sentiment_dist = sentiment_report.get("sentiment_percentages", {})
        net_score = sentiment_report.get("net_sentiment_score", 0)
        negative_pct = sentiment_dist.get("negative", 0)

        if negative_pct > 40:
            user_impact, impact_detail = "HIGH", f"{negative_pct}% negative sentiment. Users reporting crashes, payment failures, and performance issues."
        elif negative_pct > 25:
            user_impact, impact_detail = "MEDIUM", f"{negative_pct}% negative sentiment. Mixed reception with notable issues."
        else:
            user_impact, impact_detail = "LOW", f"{negative_pct}% negative sentiment. Generally positive reception."

        adoption = data_analyst_report.get("summary_statistics", {}).get("feature_adoption_funnel_pct", {})
        adoption_latest = adoption.get("post_launch_latest", 0)

        go_factors, nogo_factors = [], []
        if adoption_latest >= 20: go_factors.append(f"Feature adoption at {adoption_latest}% (meets target)")
        else: nogo_factors.append(f"Feature adoption at {adoption_latest}% (below 20% target)")
        if synthesis["failing_criteria_count"] <= 2: go_factors.append(f"Only {synthesis['failing_criteria_count']} criteria failing")
        else: nogo_factors.append(f"{synthesis['failing_criteria_count']} success criteria failing")
        if net_score > 0: go_factors.append(f"Net sentiment positive ({net_score})")
        else: nogo_factors.append(f"Net sentiment negative ({net_score})")
        dau_change = data_analyst_report.get("summary_statistics", {}).get("dau", {}).get("change_pct", 0)
        if dau_change > 0: go_factors.append(f"DAU increased {dau_change}% post-launch")
        if synthesis["critical_anomaly_count"] > 0:
            nogo_factors.append(f"{synthesis['critical_anomaly_count']} critical anomalies detected")
        high_ki = [ki for ki in ki_matches if ki["severity"] == "high" and ki["observed_in_metrics"]]
        if high_ki: nogo_factors.append(f"{len(high_ki)} high-severity known issues confirmed in production")

        if len(nogo_factors) >= 4 or (user_impact == "HIGH" and synthesis["health_score"] < 40):
            pm_rec = "ROLL_BACK"
        elif len(nogo_factors) >= 2 or user_impact == "HIGH":
            pm_rec = "PAUSE"
        else:
            pm_rec = "PROCEED"

        self.log(f"PM Assessment: Impact={user_impact}, Go={len(go_factors)}, NoGo={len(nogo_factors)}, Rec={pm_rec}")
        return {
            "agent": self.name, "feature": self.release_notes["feature_name"],
            "version": self.release_notes["version"],
            "success_criteria_evaluation": criteria_check["_summary"],
            "known_issue_correlation": ki_matches,
            "user_impact_assessment": {"level": user_impact, "detail": impact_detail, "net_sentiment_score": net_score},
            "feature_adoption": {"current_pct": adoption_latest, "trend": adoption.get("trend", "unknown"),
                "target_pct": 20.0, "meets_target": adoption_latest >= 20},
            "go_nogo_framing": {"go_factors": go_factors, "nogo_factors": nogo_factors,
                "go_count": len(go_factors), "nogo_count": len(nogo_factors)},
            "recommendation": pm_rec,
            "rollback_available": self.release_notes.get("rollback_plan", "Not documented")
        }


class MarketingCommsAgent(BaseAgent):
    """Assesses messaging, customer perception, and communication actions."""

    def __init__(self, sentiment_analyzer):
        super().__init__("MarketingCommsAgent", "Marketing & Communications")
        self.sentiment_analyzer = sentiment_analyzer

    def analyze(self, pm_report: Dict) -> Dict[str, Any]:
        self.log("Analyzing customer perception and communication needs...")
        self.log("Invoking SentimentAnalyzer.get_sentiment_summary()")
        sentiment = self.sentiment_analyzer.get_sentiment_summary()
        self.log("Invoking SentimentAnalyzer.extract_themes()")
        themes = self.sentiment_analyzer.extract_themes()
        self.log("Invoking SentimentAnalyzer.detect_urgency_signals()")
        urgency = self.sentiment_analyzer.detect_urgency_signals()

        negative_pct = sentiment["sentiment_percentages"].get("negative", 0)
        perception_risk = "HIGH" if negative_pct > 40 else "MEDIUM" if negative_pct > 25 else "LOW"

        top_complaints = sorted(
            [{"theme": name, "mention_count": d["count"], "percentage": d["percentage_of_total"],
              "channels": d["channels_affected"]}
             for name, d in themes.items() if d["count"] > 0 and name != "positive_feature_reception"],
            key=lambda x: x["mention_count"], reverse=True
        )

        decision = pm_report.get("recommendation", "PAUSE")
        comms = self._build_comms_plan(decision, top_complaints, perception_risk)

        self.log(f"Comms Assessment: Risk={perception_risk}, Themes={[c['theme'] for c in top_complaints[:3]]}")
        return {
            "agent": self.name, "sentiment_analysis": sentiment,
            "theme_analysis": themes, "urgency_signals": urgency,
            "perception_assessment": {
                "risk_level": perception_risk, "negative_sentiment_pct": negative_pct,
                "top_complaint_themes": top_complaints[:3],
                "positive_signals": themes.get("positive_feature_reception", {}).get("count", 0)
            },
            "communication_plan": comms
        }

    def _build_comms_plan(self, decision, top_complaints, perception_risk):
        plan = {"decision_context": decision, "internal_communications": [],
                "external_communications": [], "social_media_response": [], "support_team_guidance": []}
        if decision in ["PAUSE", "ROLL_BACK"]:
            plan["internal_communications"] = [
                {"audience": "Engineering", "message": "War room decision: Feature rollout paused/rolled back. Priority hotfix sprint initiated.", "channel": "Slack #engineering", "timing": "Immediate"},
                {"audience": "Customer Success", "message": "Prepare for increased inbound. Talking points and known issue guide attached.", "channel": "Slack #cs-team + Email", "timing": "Within 1 hour"},
                {"audience": "Leadership", "message": "Launch status update: Decision to pause/rollback due to stability concerns. Recovery plan in progress.", "channel": "Email + Meeting invite", "timing": "Within 2 hours"},
                {"audience": "All Hands", "message": "Feature launch update - temporary pause while we address user-reported issues.", "channel": "Slack #general", "timing": "Within 4 hours"}
            ]
            plan["external_communications"] = [
                {"audience": "Affected Users", "message": "We have identified issues with our latest update and are actively working on fixes. We apologize for the inconvenience.", "channel": "In-app banner + Email", "timing": "Within 2 hours"},
                {"audience": "All Users", "message": "We are aware of stability issues in our recent update and are prioritizing fixes. Your experience matters to us.", "channel": "Status page + Blog", "timing": "Within 4 hours"}
            ]
            plan["social_media_response"] = [
                {"platform": "Twitter", "action": "Respond to negative mentions with acknowledgment and status page link", "tone": "Empathetic, transparent, solution-focused"},
                {"platform": "App Store", "action": "Post developer response to 1-star reviews acknowledging the issue", "tone": "Professional, with fix timeline"}
            ]
            plan["support_team_guidance"] = [
                "Acknowledge the issue immediately - do not deflect",
                "Provide workaround for crash issues: disable animated charts in Settings > Display",
                "For payment failures: advise retry after 30 seconds; escalate double-charges to billing team immediately",
                "Log all contacts with issue category tags for tracking",
                "Escalate any cancellation threats to retention team"
            ]
        else:
            plan["internal_communications"] = [
                {"audience": "All Teams", "message": "Launch proceeding with monitoring.", "channel": "Slack #launch-war-room", "timing": "Immediate"}]
            plan["external_communications"] = [
                {"audience": "Users", "message": "Smart Insights is live! Check out the new analytics dashboard.", "channel": "In-app + Email", "timing": "Continue rollout comms"}]
        return plan


class RiskCriticAgent(BaseAgent):
    """Challenges assumptions, highlights risks, requests additional evidence."""

    def __init__(self):
        super().__init__("RiskCriticAgent", "Risk & Critic")

    def analyze(self, data_report, pm_report, comms_report) -> Dict[str, Any]:
        self.log("Initiating risk assessment and assumption challenging...")
        synthesis = data_report.get("synthesis", {})
        degrading = synthesis.get("degrading_metrics", [])
        risks = []

        summary_stats = data_report.get("summary_statistics", {})
        if "crash_rate_pct" in degrading:
            d = summary_stats.get("crash_rate_pct", {})
            risks.append({"id": "RISK-001", "category": "Stability", "severity": "CRITICAL",
                "description": f"Crash rate trending upward (pre: {d.get('pre_launch_avg')}% -> post: {d.get('post_launch_avg')}%). Could exceed 2.5% within 48 hours.",
                "impact": "User trust erosion, app store rating decline", "mitigation": "Deploy hotfix for Android 13 crash. Enable crash-safe mode via feature flag.", "owner": "Engineering Lead"})
        if "payment_success_rate_pct" in degrading:
            d = summary_stats.get("payment_success_rate_pct", {})
            risks.append({"id": "RISK-002", "category": "Revenue", "severity": "HIGH",
                "description": f"Payment success rate declining (pre: {d.get('pre_launch_avg')}% -> post: {d.get('post_launch_avg')}%). Direct revenue impact.",
                "impact": "Lost revenue, failed transactions, chargeback increase", "mitigation": "Rollback payment SDK to previous stable version.", "owner": "Payments Team"})
        if "api_latency_p95_ms" in degrading:
            d = summary_stats.get("api_latency_p95_ms", {})
            risks.append({"id": "RISK-003", "category": "Performance", "severity": "HIGH",
                "description": f"API latency p95 severely elevated (pre: {d.get('pre_launch_avg')}ms -> post: {d.get('post_launch_avg')}ms). Exceeds 250ms target.",
                "impact": "Poor UX, timeout cascades, downstream service degradation", "mitigation": "Optimize database queries. Add caching layer.", "owner": "Backend Engineering"})
        if "support_ticket_volume" in degrading:
            d = summary_stats.get("support_ticket_volume", {})
            risks.append({"id": "RISK-004", "category": "Operational", "severity": "MEDIUM",
                "description": f"Support ticket volume surging (pre: {d.get('pre_launch_avg')} -> post: {d.get('post_launch_avg')} daily). Team may be overwhelmed.",
                "impact": "Increased response times, lower CSAT", "mitigation": "Activate overflow support. Deploy auto-response for known issues.", "owner": "Support Team Lead"})
        if "churn_rate_pct" in degrading:
            d = summary_stats.get("churn_rate_pct", {})
            risks.append({"id": "RISK-005", "category": "Retention", "severity": "HIGH",
                "description": f"Churn rate increasing (pre: {d.get('pre_launch_avg')}% -> post: {d.get('post_launch_avg')}%). Users mentioning cancellation.",
                "impact": "MRR loss, negative word-of-mouth", "mitigation": "Proactive outreach to at-risk users. Fast-track critical fixes.", "owner": "Customer Success Lead"})
        if len(degrading) >= 3:
            risks.append({"id": "RISK-006", "category": "Systemic", "severity": "HIGH",
                "description": f"{len(degrading)} metrics degrading simultaneously. Compounding effects likely - crashes cause support surge, which increases churn.",
                "impact": "Cascading failure across stability, revenue, and retention", "mitigation": "Consider full rollback to break the chain.", "owner": "VP Engineering"})

        challenges = [
            {"assumption": "Feature adoption is positive signal", "challenge": "High adoption + high crash rate means MORE users hit bugs. Adoption without stability is a liability.",
             "evidence_needed": "Crash rate segmented by Smart Insights adopters vs non-adopters"},
            {"assumption": "DAU increase validates the launch", "challenge": "DAU increase could be curiosity-driven, not sustained value.",
             "evidence_needed": "Cohort retention analysis for Smart Insights adopters"},
            {"assumption": "Known issues have viable workarounds", "challenge": "Disabling animated charts degrades the feature value proposition.",
             "evidence_needed": "Percentage of crash-affected users who applied workaround"},
            {"assumption": "Positive feedback balances negative", "challenge": "Satisfied users may not yet have encountered device-specific bugs.",
             "evidence_needed": "Device/OS segmentation of positive vs negative feedback"},
        ]

        evidence_requests = [
            "Crash rate by device type and OS version",
            "Payment failure rate by time of day and method",
            "Funnel drop-off analysis for Smart Insights",
            "Server-side error logs from past 48 hours",
            "A/B comparison if control group exists"
        ]

        severity_w = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 4, "LOW": 1}
        risk_score = sum(severity_w.get(r["severity"], 0) for r in risks)
        max_p = len(risks) * 10 if risks else 1
        normalized = round(risk_score / max_p * 100, 1)

        critic_rec = "ROLL_BACK" if (normalized > 70 or any(r["severity"] == "CRITICAL" for r in risks)) else                      "PAUSE" if normalized > 40 else "PROCEED"

        self.log(f"Risk Assessment: {len(risks)} risks, score={normalized}/100, rec={critic_rec}")
        return {
            "agent": self.name, "risk_register": risks,
            "risk_summary": {"total_risks": len(risks),
                "critical": sum(1 for r in risks if r["severity"] == "CRITICAL"),
                "high": sum(1 for r in risks if r["severity"] == "HIGH"),
                "medium": sum(1 for r in risks if r["severity"] == "MEDIUM"),
                "low": sum(1 for r in risks if r["severity"] == "LOW"),
                "overall_risk_score": normalized},
            "assumption_challenges": challenges,
            "additional_evidence_requested": evidence_requests,
            "recommendation": critic_rec
        }


class SREAgent(BaseAgent):
    """(Bonus Agent) Assesses infrastructure health and rollback readiness."""

    def __init__(self, release_notes: Dict):
        super().__init__("SREAgent", "Site Reliability Engineering")
        self.release_notes = release_notes

    def analyze(self, data_report: Dict) -> Dict[str, Any]:
        self.log("Assessing infrastructure health and rollback readiness...")
        latency = data_report.get("summary_statistics", {}).get("api_latency_p95_ms", {})
        crash = data_report.get("summary_statistics", {}).get("crash_rate_pct", {})
        lp = latency.get("post_launch_avg", 0)
        cp = crash.get("post_launch_avg", 0)
        status = "DEGRADED" if (lp > 400 or cp > 2.0) else "WARNING" if (lp > 250 or cp > 1.0) else "HEALTHY"
        rollback_plan = self.release_notes.get("rollback_plan", "")
        rollback_ready = "feature flag" in rollback_plan.lower() or "backward-compatible" in rollback_plan.lower()
        synthesis = data_report.get("synthesis", {})
        self.log(f"SRE Assessment: status={status}, rollback_ready={rollback_ready}")
        return {
            "agent": self.name, "system_status": status,
            "infrastructure_assessment": {
                "api_latency_status": "CRITICAL" if lp > 400 else "WARNING" if lp > 250 else "OK",
                "crash_rate_status": "CRITICAL" if cp > 2.0 else "WARNING" if cp > 1.0 else "OK",
                "current_p95_latency_ms": round(lp, 1), "current_crash_rate_pct": round(cp, 2)},
            "rollback_readiness": {
                "is_ready": rollback_ready, "mechanism": rollback_plan,
                "estimated_rollback_time": "< 15 minutes (feature flag toggle)" if rollback_ready else "30-60 minutes",
                "data_migration_safe": "backward-compatible" in rollback_plan.lower()},
            "capacity_assessment": {
                "support_queue": "OVERLOADED" if synthesis.get("health_score", 50) < 40 else "MANAGEABLE",
                "engineering_bandwidth": "Hotfix sprint required" if status != "HEALTHY" else "Normal operations"}
        }
