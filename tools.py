"""
tools.py - Programmatic tools invoked by war room agents
========================================================
Tool 1: MetricAnalyzer  - aggregation, trend detection, threshold checks
Tool 2: SentimentAnalyzer - sentiment analysis + theme extraction
Tool 3: AnomalyDetector - statistical anomaly detection on time series
"""

import csv
import json
import math
from typing import Dict, List, Any


class MetricAnalyzer:
    """Analyzes time-series metrics from the mock dashboard."""

    def __init__(self, csv_path: str, success_criteria: Dict[str, str]):
        self.data = self._load_csv(csv_path)
        self.success_criteria = success_criteria
        self.metric_columns = [
            "signup_conversion_pct", "dau", "wau", "retention_d1_pct",
            "retention_d7_pct", "crash_rate_pct", "api_latency_p95_ms",
            "payment_success_rate_pct", "support_ticket_volume",
            "feature_adoption_funnel_pct", "churn_rate_pct"
        ]
        print("[TOOL CALL] MetricAnalyzer initialized with", len(self.data), "days of data")

    def _load_csv(self, path: str) -> List[Dict]:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                for key in row:
                    if key not in ("date", "phase"):
                        try:
                            row[key] = float(row[key])
                        except ValueError:
                            pass
                rows.append(row)
        return rows

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Compute pre-launch vs post-launch summary for all metrics."""
        print("[TOOL CALL] MetricAnalyzer.get_summary_statistics()")
        pre = [r for r in self.data if r["phase"] == "pre_launch"]
        post = [r for r in self.data if r["phase"] == "post_launch"]
        summary = {}
        for col in self.metric_columns:
            pre_vals = [r[col] for r in pre]
            post_vals = [r[col] for r in post]
            pre_avg = sum(pre_vals) / len(pre_vals) if pre_vals else 0
            post_avg = sum(post_vals) / len(post_vals) if post_vals else 0
            change_pct = ((post_avg - pre_avg) / pre_avg * 100) if pre_avg != 0 else 0
            summary[col] = {
                "pre_launch_avg": round(pre_avg, 2),
                "post_launch_avg": round(post_avg, 2),
                "change_pct": round(change_pct, 2),
                "post_launch_min": round(min(post_vals), 2) if post_vals else None,
                "post_launch_max": round(max(post_vals), 2) if post_vals else None,
                "post_launch_latest": round(post_vals[-1], 2) if post_vals else None,
                "trend": self._compute_trend(post_vals)
            }
        return summary

    def check_success_criteria(self) -> Dict[str, Any]:
        """Check each success criterion against latest post-launch data."""
        print("[TOOL CALL] MetricAnalyzer.check_success_criteria()")
        post = [r for r in self.data if r["phase"] == "post_launch"]
        if not post:
            return {"error": "No post-launch data available"}
        latest = post[-1]
        criteria_map = {
            "signup_conversion": ("signup_conversion_pct", ">=", 12.0),
            "feature_adoption_funnel": ("feature_adoption_funnel_pct", ">=", 20.0),
            "crash_rate": ("crash_rate_pct", "<", 1.0),
            "api_latency_p95": ("api_latency_p95_ms", "<", 250.0),
            "payment_success_rate": ("payment_success_rate_pct", ">=", 98.5),
            "support_ticket_volume": ("support_ticket_volume", "<", 100.0),
            "churn_rate": ("churn_rate_pct", "<", 2.5),
        }
        results = {}
        passing = 0
        failing = 0
        for name, (col, op, threshold) in criteria_map.items():
            actual = latest[col]
            if op == ">=":
                met = actual >= threshold
            else:
                met = actual < threshold
            if met:
                passing += 1
            else:
                failing += 1
            results[name] = {
                "metric": col, "threshold": f"{op} {threshold}",
                "actual_value": round(actual, 2),
                "status": "PASS" if met else "FAIL",
                "gap": round(actual - threshold, 2) if not met else 0
            }
        results["_summary"] = {
            "total_criteria": len(criteria_map),
            "passing": passing, "failing": failing,
            "pass_rate_pct": round(passing / len(criteria_map) * 100, 1)
        }
        return results

    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze trends for each metric over the post-launch period."""
        print("[TOOL CALL] MetricAnalyzer.get_trend_analysis()")
        post = [r for r in self.data if r["phase"] == "post_launch"]
        trends = {}
        for col in self.metric_columns:
            vals = [r[col] for r in post]
            trends[col] = {
                "values": [round(v, 2) for v in vals],
                "trend_direction": self._compute_trend(vals),
                "volatility": round(self._std_dev(vals), 3) if len(vals) > 1 else 0
            }
        return trends

    def _compute_trend(self, values):
        if len(values) < 2:
            return "insufficient_data"
        diffs = [values[i] - values[i-1] for i in range(1, len(values))]
        avg_diff = sum(diffs) / len(diffs)
        if avg_diff > 0.5:
            return "increasing"
        elif avg_diff < -0.5:
            return "decreasing"
        return "stable"

    def _std_dev(self, values):
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)


class SentimentAnalyzer:
    """Analyzes user feedback for sentiment, themes, and urgency."""

    NEGATIVE_KEYWORDS = ["crash", "broken", "failed", "slow", "bug", "error",
        "unacceptable", "frustrating", "cancel", "terrible", "worst", "ruined",
        "timeout", "lost", "charged twice"]
    POSITIVE_KEYWORDS = ["love", "great", "excellent", "amazing", "impressive",
        "clean", "intuitive", "useful", "best", "game changer", "saving", "solid"]
    URGENCY_KEYWORDS = ["asap", "immediately", "urgent", "cancel", "unacceptable",
        "considering cancellation", "charged twice"]
    THEME_PATTERNS = {
        "crash_instability": ["crash", "dies", "blank screen", "crashes"],
        "payment_issues": ["payment", "charged", "checkout", "gateway", "transaction"],
        "performance_latency": ["slow", "latency", "takes forever", "5+ seconds", "painfully slow"],
        "positive_feature_reception": ["love", "great", "impressive", "game changer", "useful"],
        "onboarding_ux": ["onboarding", "tutorial", "docs", "understand", "getting used to"],
        "data_reliability": ["doesn't refresh", "errors", "data", "lost"],
    }

    def __init__(self, feedback_path: str):
        with open(feedback_path, "r") as f:
            self.feedback = json.load(f)
        print("[TOOL CALL] SentimentAnalyzer initialized with", len(self.feedback), "feedback entries")

    def get_sentiment_summary(self) -> Dict[str, Any]:
        """Compute overall sentiment distribution and stats."""
        print("[TOOL CALL] SentimentAnalyzer.get_sentiment_summary()")
        total = len(self.feedback)
        dist = {"positive": 0, "negative": 0, "neutral": 0}
        for fb in self.feedback:
            dist[fb["sentiment_label"]] += 1
        channel_sentiment = {}
        for fb in self.feedback:
            ch = fb["channel"]
            if ch not in channel_sentiment:
                channel_sentiment[ch] = {"positive": 0, "negative": 0, "neutral": 0}
            channel_sentiment[ch][fb["sentiment_label"]] += 1
        ratings = [fb["rating"] for fb in self.feedback if fb["rating"] is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        return {
            "total_feedback": total,
            "sentiment_distribution": dist,
            "sentiment_percentages": {k: round(v / total * 100, 1) for k, v in dist.items()},
            "average_rating": avg_rating,
            "channel_breakdown": channel_sentiment,
            "net_sentiment_score": round((dist["positive"] - dist["negative"]) / total * 100, 1)
        }

    def extract_themes(self) -> Dict[str, Any]:
        """Extract recurring themes from feedback."""
        print("[TOOL CALL] SentimentAnalyzer.extract_themes()")
        themes = {}
        for theme_name, keywords in self.THEME_PATTERNS.items():
            matching = []
            for fb in self.feedback:
                text_lower = fb["text"].lower()
                if any(kw in text_lower for kw in keywords):
                    matching.append({"id": fb["id"], "text": fb["text"],
                        "sentiment": fb["sentiment_label"], "channel": fb["channel"]})
            themes[theme_name] = {
                "count": len(matching),
                "percentage_of_total": round(len(matching) / len(self.feedback) * 100, 1),
                "examples": matching[:3],
                "channels_affected": list(set(m["channel"] for m in matching))
            }
        return dict(sorted(themes.items(), key=lambda x: x[1]["count"], reverse=True))

    def detect_urgency_signals(self) -> Dict[str, Any]:
        """Identify high-urgency feedback needing immediate attention."""
        print("[TOOL CALL] SentimentAnalyzer.detect_urgency_signals()")
        urgent = []
        for fb in self.feedback:
            text_lower = fb["text"].lower()
            urgency_matches = [kw for kw in self.URGENCY_KEYWORDS if kw in text_lower]
            if urgency_matches:
                urgent.append({"id": fb["id"], "text": fb["text"],
                    "channel": fb["channel"], "triggers": urgency_matches})
        return {
            "urgent_count": len(urgent),
            "urgent_percentage": round(len(urgent) / len(self.feedback) * 100, 1),
            "urgent_items": urgent
        }


class AnomalyDetector:
    """Detects statistical anomalies using z-score against pre-launch baseline."""

    def __init__(self, csv_path: str, z_threshold: float = 2.0):
        self.z_threshold = z_threshold
        self.data = self._load_csv(csv_path)
        self.metric_columns = [
            "signup_conversion_pct", "dau", "wau", "retention_d1_pct",
            "retention_d7_pct", "crash_rate_pct", "api_latency_p95_ms",
            "payment_success_rate_pct", "support_ticket_volume",
            "feature_adoption_funnel_pct", "churn_rate_pct"
        ]
        print("[TOOL CALL] AnomalyDetector initialized (z_threshold=" + str(z_threshold) + ")")

    def _load_csv(self, path):
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                for key in row:
                    if key not in ("date", "phase"):
                        try:
                            row[key] = float(row[key])
                        except ValueError:
                            pass
                rows.append(row)
        return rows

    def detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in post-launch data using pre-launch baseline."""
        print("[TOOL CALL] AnomalyDetector.detect_anomalies()")
        pre = [r for r in self.data if r["phase"] == "pre_launch"]
        post = [r for r in self.data if r["phase"] == "post_launch"]
        anomalies = {}
        total_anomaly_count = 0
        for col in self.metric_columns:
            pre_vals = [r[col] for r in pre]
            mean = sum(pre_vals) / len(pre_vals) if pre_vals else 0
            std = self._std_dev(pre_vals) if len(pre_vals) > 1 else 1
            if std == 0:
                std = 0.001
            col_anomalies = []
            for r in post:
                val = r[col]
                z_score = (val - mean) / std
                if abs(z_score) > self.z_threshold:
                    col_anomalies.append({
                        "date": r["date"], "day": int(r["day"]),
                        "value": round(val, 2), "baseline_mean": round(mean, 2),
                        "baseline_std": round(std, 3), "z_score": round(z_score, 2),
                        "direction": "above" if z_score > 0 else "below",
                        "severity": "critical" if abs(z_score) > 3.0 else "warning"
                    })
                    total_anomaly_count += 1
            if col_anomalies:
                anomalies[col] = {"anomaly_count": len(col_anomalies), "anomalies": col_anomalies}
        return {
            "total_anomalies_detected": total_anomaly_count,
            "metrics_with_anomalies": len(anomalies),
            "z_threshold": self.z_threshold,
            "anomalies_by_metric": anomalies
        }

    def _std_dev(self, values):
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
