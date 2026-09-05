TRACK_ID=PS02

# ClaimGuard AI

Insurance Claims Evidence Review Assistant.

## What it does

ClaimGuard AI reviews motor insurance claims against a generated insurance
policy and supporting evidence.

It checks:

- Claim completeness
- Required documents
- Policy coverage
- Claim windows
- Insured value
- Contradictions between documents
- Evidence supporting each finding
- Uncertainty and escalation

The system recommends:

- APPROVE
- REJECT
- REQUEST INFORMATION
- ESCALATE

The system does not make unsupported decisions or invent missing evidence.

## How to run

```bash
pip install -r requirements.txt
python app.py