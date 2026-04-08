# PurpleMerit War Room — Multi-Agent Launch Decision System
: 
>Build a multi-agent system that simulates a cross-functional "war room" during a product launch.

## Overview

This system simulates coordinated decision-making among 5 specialized AI agents during a product launch crisis. Given a mock dashboard of metrics, user feedback, and release notes, the system produces a structured launch decision (**Proceed / Pause / Roll Back**) along with a comprehensive action plan.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   WAR ROOM ORCHESTRATOR                  │
│            (Coordinator / Decision Synthesizer)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: DataAnalystAgent ──→ MetricAnalyzer (Tool)    │
│                             ──→ AnomalyDetector (Tool)  │
│                                                         │
│  Phase 2: MarketingCommsAgent ──→ SentimentAnalyzer     │
│                               ──→ Theme Extractor       │
│                               ──→ Urgency Detector      │
│                                                         │
│  Phase 3: ProductManagerAgent ──→ Uses Phase 1 & 2      │
│                               ──→ Success Criteria Map  │
│                               ──→ Known Issue Correlator│
│                                                         │
│  Phase 4: SREAgent (Bonus) ──→ Infrastructure Health    │
│                             ──→ Rollback Readiness      │
│                                                         │
│  Phase 5: RiskCriticAgent ──→ All previous reports      │
│                           ──→ Assumption Challenger     │
│                           ──→ Evidence Requester        │
│                                                         │
│  Phase 6: Orchestrator ──→ Weighted Decision Synthesis  │
│                        ──→ Structured JSON Output       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility | Tools Used |
|---|---|---|
| **DataAnalystAgent** | Quantitative metrics analysis, trends, anomalies, success criteria checking | `MetricAnalyzer`, `AnomalyDetector` |
| **ProductManagerAgent** | User impact assessment, go/no-go framing, known issue correlation | Release notes cross-referencing |
| **MarketingCommsAgent** | Customer perception, sentiment analysis, communication planning | `SentimentAnalyzer` (summary, themes, urgency) |
| **RiskCriticAgent** | Risk identification, assumption challenging, evidence requests | All agent reports |
| **SREAgent** *(Bonus)* | Infrastructure health, rollback readiness, operational capacity | System metrics analysis |

## Tools

| Tool | Capabilities | Called By |
|---|---|---|
| **MetricAnalyzer** | Summary statistics, pre/post comparison, trend detection, success criteria threshold checks | DataAnalystAgent |
| **AnomalyDetector** | Z-score based anomaly detection against pre-launch baseline | DataAnalystAgent |
| **SentimentAnalyzer** | Sentiment distribution, keyword-based theme extraction, urgency signal detection | MarketingCommsAgent |

## Project Structure

```
purplemerit-war-room/
├── main.py                  # Entry point - CLI application
├── orchestrator.py          # War Room Orchestrator (coordinator)
├── agents.py                # All 5 agent implementations
├── tools.py                 # 3 analytical tools
├── data/
│   ├── mock_metrics.csv     # 14-day time-series (11 metrics)
│   ├── user_feedback.json   # 40 feedback entries (pos/neg/neutral)
│   └── release_notes.json   # Feature description + known issues
├── output/
│   ├── war_room_decision.json   # Final structured decision
│   └── trace_log.txt            # Full execution trace
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- No external LLM API keys required (the system uses deterministic analysis)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/purplemerit-war-room.git
cd purplemerit-war-room

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
No environment variables are required. The system operates fully offline using deterministic analysis tools.

## How to Run

### Basic Usage
```bash
python main.py
```

### Custom Paths
```bash
python main.py \
  --metrics data/mock_metrics.csv \
  --feedback data/user_feedback.json \
  --release-notes data/release_notes.json \
  --output output/war_room_decision.json \
  --trace-output output/trace_log.txt
```

### Example Output
```
======================================================================
                    WAR ROOM DECISION SUMMARY
======================================================================
  Feature:        Smart Insights Dashboard v4.2.0
  Decision:       >>> ROLL_BACK <<<
  Confidence:     95%
  Risks:          3 identified
  Actions:        9 planned

  Agent Recommendations:
    - DataAnalyst         : ROLL_BACK
    - ProductManager      : ROLL_BACK
    - RiskCritic          : PAUSE
======================================================================
```

## Output Format

The system produces a JSON file (`output/war_room_decision.json`) containing:

| Field | Description |
|---|---|
| `decision` | `PROCEED` / `PAUSE` / `ROLL_BACK` |
| `rationale` | Key drivers with metric references + feedback summary |
| `risk_register` | Top risks with severity, impact, mitigation, and owner |
| `action_plan` | 24-48 hour action items with timeframes, owners, and priorities |
| `communication_plan` | Internal + external messaging guidance |
| `confidence` | Score (0-100%) + factors + what would increase confidence |
| `agent_recommendations` | Individual recommendations from each agent |
| `detailed_reports` | Per-agent analysis summaries |

## Traceability

- **Console Logs**: All agent steps and tool invocations are printed in real-time during execution
- **Trace File**: `output/trace_log.txt` contains timestamped logs of every agent action and tool call
- Each log entry includes: `[timestamp] [AgentName] action description`
- Tool calls are explicitly logged: `[TOOL CALL] ToolName.method()`

## Mock Data Description

### Metrics (14 days)
- **Pre-launch** (Days 1-7): Stable baseline performance
- **Post-launch** (Days 8-14): Feature launch causes metric shifts
  - Crash rate increases from ~0.4% to ~1.5%
  - API latency spikes from ~200ms to ~400ms+
  - Payment success rate drops from ~98.7% to ~97%
  - Support tickets surge from ~45/day to ~110/day
  - Feature adoption grows to ~35%
  - DAU increases due to new feature interest

### User Feedback (40 entries)
- 12 positive (love the feature, great UX)
- 18 negative (crashes, payment failures, slow performance)
- 10 neutral (mixed feelings, undecided)
- Repeated themes: crashes on Android 13, payment issues, latency

### Known Issues (4)
- KI-001: Android 13 crash (HIGH)
- KI-002: Payment gateway timeout (MEDIUM)
- KI-003: API latency above target (MEDIUM)
- KI-004: Tablet UI overlap (LOW)

## Design Decisions

1. **No LLM dependency**: Tools use statistical analysis and keyword-based NLP to ensure reproducibility and zero API cost
2. **Weighted voting**: Final decision uses weighted votes from all agents + SRE system status as a modifier
3. **Z-score anomaly detection**: Pre-launch data establishes baseline; post-launch values compared using z-scores (threshold: 2.0)
4. **Deterministic output**: Same inputs always produce the same decision (no randomness in analysis)

## Reproducing the Output

```bash
# Run the system
python main.py

# View the decision
cat output/war_room_decision.json | python -m json.tool

# View the trace
cat output/trace_log.txt
```

## License
MIT
