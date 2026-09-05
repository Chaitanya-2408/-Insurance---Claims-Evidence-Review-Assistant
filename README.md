TRACK_ID=PS02

# ClaimGuard AI

## Insurance Claims Evidence Review Assistant

ClaimGuard AI is a reviewer-focused AI-assisted system for reviewing motor
insurance claims against a policy and supporting evidence.

It combines **deterministic insurance rules** with **Gemini 3.1 Flash-Lite**
to produce grounded claim-review summaries, evidence findings, contradictions,
and recommendations.

---

## What it does

ClaimGuard AI reviews a motor insurance claim against the policy and available
supporting evidence.

It checks:

- Claim completeness
- Required documents
- Policy coverage
- Claim reporting window
- Insured Declared Value (IDV)
- Policy exclusions
- Contradictions between evidence
- Evidence supporting each finding
- Uncertainty and escalation conditions

The system produces one of four recommendations:

- `APPROVE`
- `REJECT`
- `REQUEST_INFORMATION`
- `ESCALATE`

The system does **not** invent missing evidence or allow the LLM to override
deterministic policy findings.

---

## Key Features

### 1. Deterministic claim validation

Core policy checks are implemented as deterministic Python rules.

Examples:

- Required-document validation
- 7-day accident reporting window
- IDV limit validation
- Policy exclusion checks
- Contradiction detection
- Uncertain incident-cause detection

This keeps critical decision logic predictable and auditable.

### 2. Grounded GenAI review

Gemini 3.1 Flash-Lite is used to generate a reviewer-friendly explanation
from:

- Claim information
- Deterministic findings
- Retrieved policy sections
- Supporting evidence

The generated explanation is grounded in the supplied policy and claim
evidence.

### 3. Local policy retrieval

Policy sections are embedded using:

`gemini-embedding-001`

Embeddings are stored and searched locally using NumPy cosine similarity.

No hosted vector database is required.

### 4. Evidence uploads

New claims can be submitted using:

- Claim Form — PDF/TXT
- Repair Estimate — PDF/TXT
- FIR — PDF/TXT
- Incident Description — manual text

PDF text is extracted locally using `pypdf`.

Maximum upload size: **5 MB per file**.

### 5. Graceful AI fallback

If Gemini is unavailable because of:

- API errors
- Rate limits
- Invalid credentials
- Temporary service failures

the deterministic review logic still produces the claim decision and
evidence findings.

---

## Review Decision Logic

The deterministic review layer follows the policy rules before the AI
explanation is generated.

| Condition | Recommendation |
|---|---|
| Evidence complete, covered, within limits, no contradictions | `APPROVE` |
| Potentially covered but required information is missing | `REQUEST_INFORMATION` |
| Clearly excluded under policy | `REJECT` |
| Material contradiction or significant uncertainty | `ESCALATE` |

AI-generated explanations do not override these deterministic decisions.

---

## Demo Claims

The project includes six predefined claim scenarios designed to demonstrate
different review outcomes.

| Claim | Scenario | Expected Decision |
|---|---|---|
| CLM-001 | Valid collision claim | `APPROVE` |
| CLM-002 | Missing Repair Estimate | `REQUEST_INFORMATION` |
| CLM-003 | Mechanical breakdown exclusion | `REJECT` |
| CLM-004 | Material evidence contradiction | `ESCALATE` |
| CLM-005 | Late claim reporting | `ESCALATE` |
| CLM-006 | Uncertain incident cause | `ESCALATE` |

These claims are available in:

`data/claims/`

---

## Reviewer Demo Documents

The repository also contains ready-to-upload fictional evidence documents
for demonstrating the document-upload workflow.

Location:

`demo_documents/`

Included formats:

- `claim_form.pdf`
- `claim_form.txt`
- `repair_estimate.pdf`
- `repair_estimate.txt`
- `incident_description.pdf`
- `incident_description.txt`
- `fir.pdf`
- `fir.txt`

The demo evidence represents a fictional collision claim for INR 145,000.

### Recommended upload demo

For a collision claim, upload:

1. `claim_form.pdf`
2. `repair_estimate.pdf`
3. `incident_description.pdf`

The same documents are also available as TXT files for testing the TXT
upload path.

> All documents in `demo_documents/` are fictional demonstration/test inputs
> and are not real insurance or police documents.

---

## Architecture

```text
                    ┌──────────────────────┐
                    │   Reviewer / User    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Flask Web App     │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────────┐        ┌──────────────────┐
       │ Document Parser  │        │ Claim Validation │
       │ PDF / TXT        │        │ & Normalization  │
       └────────┬─────────┘        └────────┬─────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
                    ┌──────────────────────┐
                    │ Deterministic Rules  │
                    │ Coverage / Docs /    │
                    │ Window / IDV / etc.  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Local Policy Search  │
                    │ Gemini Embeddings +  │
                    │ NumPy Similarity     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Gemini 3.1 Flash-Lite│
                    │ Grounded Explanation │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Final Reviewer Output│
                    │ Decision + Findings  │
                    │ Evidence + Uncertainty│
                    └──────────────────────┘