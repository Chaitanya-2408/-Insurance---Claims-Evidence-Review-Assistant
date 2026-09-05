TRACK_ID=PS02

# ClaimGuard AI
## Insurance Claims Evidence Review Assistant

ClaimGuard AI is an AI-assisted insurance claim review system designed to help
reviewers evaluate motor insurance claims against policy rules and supporting
evidence.

The system combines deterministic insurance rules, local policy retrieval,
document evidence extraction, and Gemini 3.1 Flash-Lite to produce grounded
claim-review results with findings, contradictions, citations, uncertainty
handling, and recommendations.

---

## 1. Problem

Insurance claim review often requires checking multiple pieces of information
against policy conditions:

- Claim form
- Repair estimate
- FIR where applicable
- Incident description
- Incident and reporting dates
- Claimed amount
- Coverage and exclusions
- Policy limits
- Evidence consistency

Manual review can be time-consuming, and inconsistencies or missing evidence
may be overlooked.

ClaimGuard AI provides a structured first-level review while keeping
deterministic policy rules authoritative.

---

## 2. Solution

ClaimGuard AI follows a hybrid review approach:

1. Validate the submitted claim.
2. Extract evidence from PDF/TXT documents.
3. Apply deterministic insurance rules.
4. Retrieve relevant sections from the local policy.
5. Use Gemini 3.1 Flash-Lite for grounded reasoning.
6. Identify missing information and contradictions.
7. Produce a structured recommendation.
8. Escalate uncertain or contradictory cases instead of guessing.

---

## 3. Key Features

### Deterministic Policy Validation

The system checks:

- Required documents
- Reporting window
- Coverage
- Policy exclusions
- Insured Declared Value (IDV)
- Claim amount
- Contradictions
- Uncertain incident causes

Deterministic findings remain authoritative over AI-generated reasoning.

### Grounded GenAI

Gemini 3.1 Flash-Lite receives only the relevant claim information,
policy evidence, and deterministic findings.

The model is instructed not to invent missing facts or override deterministic
policy findings.

### Local Policy Retrieval

The motor insurance policy is stored locally.

Relevant policy sections are retrieved using:

- Gemini embeddings
- `gemini-embedding-001`
- NumPy cosine similarity

No hosted vector database is required.

### Evidence Uploads

Reviewers can submit:

- PDF Claim Form
- PDF Repair Estimate
- PDF FIR
- TXT versions of the same documents

The application extracts readable text locally before review.

### Graceful AI Fallback

If Gemini is unavailable because of quota, network, or API errors, the
deterministic review pipeline continues to provide a safe fallback result.

### Reviewer-Friendly Interface

The web interface provides:

- Demo claim selection
- New claim review
- Document uploads
- Manual evidence entry
- Structured findings
- Missing information
- Contradictions
- Policy citations
- Final recommendation

---

## 4. Decision Logic

ClaimGuard AI uses four primary recommendations:

| Decision | Meaning |
|---|---|
| `APPROVE` | Evidence supports the claim and no blocking policy issue is found |
| `REJECT` | The claim is clearly excluded or outside applicable policy conditions |
| `REQUEST_INFORMATION` | The claim may be covered but required information/evidence is missing |
| `ESCALATE` | Material contradiction, uncertainty, or significant manual-review condition exists |

The system does not make a fraud determination.

---

## 5. Policy Used

The demo application uses a local motor insurance policy:

**Policy ID:** `CG-MOTOR-2026-001`

The policy contains rules covering:

- Collision
- Fixed/stationary object damage
- Overturning
- Accidental fire
- Theft
- Natural events
- Insured Declared Value
- Reporting timelines
- Required documents
- Exclusions
- Claim amount limits
- Contradiction handling
- Manual review conditions

Important findings are linked back to the relevant policy section and
supporting evidence.

---

## 6. Demo Claims

Six predefined claims are included for demonstration.

| Claim | Scenario | Expected Result |
|---|---|---|
| `CLM-001` | Valid collision claim | `APPROVE` |
| `CLM-002` | Missing repair estimate | `REQUEST_INFORMATION` |
| `CLM-003` | Excluded mechanical breakdown | `REJECT` |
| `CLM-004` | Material evidence contradiction | `ESCALATE` |
| `CLM-005` | Late claim reporting | `ESCALATE` |
| `CLM-006` | Uncertain incident cause | `ESCALATE` |

These cases demonstrate both normal processing and edge-case handling.

---

## 7. Demo Documents

The repository also contains fictional demonstration documents in:

```text
demo_documents/
    claim_form.pdf
    repair_estimate.pdf
    incident_description.pdf
    fir.pdf
```
## 8. Architecture
```text

                    ┌──────────────────────┐
                    │     Web Interface    │
                    │      Flask + HTML    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Input Validation   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Document Extraction  │
                    │      PDF / TXT       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Deterministic Rules  │
                    │ Coverage / Docs /    │
                    │ Dates / Amount / etc │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    ▼                      ▼
          ┌──────────────────┐   ┌────────────────────┐
          │ Local Policy     │   │ Gemini 3.1         │
          │ Retrieval        │   │ Flash-Lite         │
          │ + Embeddings     │   │ Grounded Reasoning │
          └────────┬─────────┘   └─────────┬──────────┘
                   │                       │
                   └───────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Structured Review    │
                    │ Findings + Evidence  │
                    │ + Recommendation     │
                    └──────────────────────┘

```
## 9. Project Structure
```text

ClaimGuard-AI/
│
├── app.py
├── README.md
├── requirements.txt
├── .env.example
│
├── data/
│   ├── policy/
│   │   └── motor_policy.txt
│   │
│   └── claims/
│       ├── claim_001.json
│       ├── claim_002.json
│       ├── claim_003.json
│       ├── claim_004.json
│       ├── claim_005.json
│       └── claim_006.json
│
├── demo_documents/
│   ├── claim_form.pdf
│   ├── repair_estimate.pdf
│   ├── incident_description.pdf
│   ├── fir.pdf
│   └── TXT versions
│
├── src/
│   ├── document_parser.py
│   ├── llm.py
│   ├── retrieval.py
│   ├── rules.py
│   ├── schemas.py
│   ├── service.py
│   └── validation.py
│
└── static/
    └── index.html

```


## 10.Technology Stack

```text

| Component      | Technology               |
| -------------- | ------------------------ |
| Backend        | Python + Flask           |
| Frontend       | HTML + CSS + JavaScript  |
| LLM            | Gemini 3.1 Flash-Lite    |
| Embeddings     | `gemini-embedding-001`   |
| Retrieval      | NumPy cosine similarity  |
| Validation     | Pydantic                 |
| PDF Extraction | PyPDF                    |
| Data           | JSON + local policy text |
| API            | Gemini API               |

```
## 11. Safety and Grounding
```text

ClaimGuard AI follows several safeguards:

- Deterministic policy rules are authoritative.
- Gemini cannot override deterministic blocking findings.
- The model receives only supplied claim and policy evidence.
- The system does not invent missing information.
- Important findings are connected to evidence and policy sections.
- Contradictions are surfaced instead of silently resolved.
- Significant uncertainty results in escalation.
- The system does not determine fraud.

The AI component assists the reviewer rather than replacing final human
judgement.
```

## 12. Engineering Approach

```text

Deterministic Layer
        │
        ├── Input validation
        ├── Required evidence checks
        ├── Date calculations
        ├── Coverage checks
        ├── Exclusion checks
        ├── IDV checks
        └── Contradiction / uncertainty checks
                    │
                    ▼
             Grounded AI Layer
                    │
                    ├── Policy context
                    ├── Evidence context
                    └── Reviewer-friendly explanation
```


