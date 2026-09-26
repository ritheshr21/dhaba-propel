# Dhaba Support Triage

A small FastAPI service that triages customer support tickets for Dhaba, a fictional subscription-based food app. It categorises tickets, assigns severity, drafts replies, flags cases for human review, and keeps refund decisions separate from the model-generated response.

## Features

* `POST /triage` endpoint for support ticket triage.
* Structured output with category, severity, refund decision, reply draft, human-review flag, and confidence.
* Fixture-based replay mode that works without an API key.
* Validation and fallback handling for invalid model output.
* A separate refund gate that does not allow the model to independently approve a refund.
* Tests for triage behaviour and refund-gate edge cases.

## Tech Stack

* Python
* FastAPI
* Pydantic
* Pytest

## Project Structure

```text
dhaba-propel/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── pipeline.py
│   ├── refund_gate.py
│   └── providers/
│       ├── base.py
│       ├── factory.py
│       ├── fixture.py
│       └── live.py
├── fixtures/
│   └── llm/
│       ├── T-1001.json
│       ├── ...
│       └── T-1012.json
├── tests/
├── dhaba_tickets.json
├── requirements.txt
└── README.md
```

## Setup and Running Locally

### Requirements

* Python 3.10 or a compatible Python version.
* pip

### 1. Clone the repository

```bash
git clone https://github.com/ritheshr21/dhaba-propel.git
cd dhaba-propel
```

### 2. Create and activate a virtual environment

**Windows — PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the service

```bash
uvicorn app.main:app --reload
```

The service should be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The fixture/replay provider is intended to let the evaluator run the service without a paid API key.

### 5. Run the tests

```bash
pytest -q
```

The test suite passed in the latest local run.

### 6. Try the endpoint

Send a `POST` request to:

```text
http://127.0.0.1:8000/triage
```

Use a ticket object from `dhaba_tickets.json` as the request body, preserving the ticket's original fields.

Example using `curl` with a saved ticket payload:

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d @ticket.json
```

Here, `ticket.json` should contain one ticket from the supplied dataset.

## Task 1 — The Service

### Triage pipeline

The service accepts a ticket and produces a structured triage result. The pipeline separates ticket understanding from refund authorisation.

The response includes:

* **Category:** the type of issue, such as billing, technical, account, cancellation, or feature request.
* **Severity:** the urgency of the issue.
* **Refund:** the refund decision, reason, and applicable amount where determined.
* **Reply draft:** a suggested response in the user's language.
* **Needs human:** whether a person should review the case.
* **Confidence:** the confidence associated with the triage result.

### Structured output and failure handling

Model output cannot be trusted to always follow the expected schema. It may be malformed, incomplete, or contain a category outside the allowed set.

The pipeline validates the output and handles invalid results through its validation, retry, and fallback path rather than blindly passing malformed output to the support tool.

### Refund safety

Refund decisions are handled by a separate gate in `app/refund_gate.py`.

The gate looks for refund-related language and checks the available payment information. A refund is not automatically approved just because a model-generated response suggests one.

The current decision behaviour includes:

* No refund request detected: `none`, reason `no_refund_request`.
* Refund request without a successful payment: `none`, reason `no_successful_payment`.
* Refund request with a successful payment: `undetermined`, reason `policy_review_required`.

An `undetermined` result means the case needs further review; it does not authorise a refund.

The refund gate uses a phrase-based heuristic. It is deliberately conservative, but it is not a complete natural-language understanding system and may miss refund requests phrased in ways its keyword list does not cover.

### Fixture mode

Fixture mode uses saved responses so the evaluator can run the service without making external model calls or spending API tokens.

The live provider is currently a placeholder, not a completed live-model integration. The offline fixture path is the intended evaluation path.

## Task 2 — Make It Not Lie

### Results from all 12 tickets

All 12 tickets returned HTTP 200 in the local fixture run.

| Ticket | Category        | Severity | Refund decision                         | Needs human | Do I agree?                                                                                                                           |
| ------ | --------------- | -------- | --------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| T-1001 | billing         | high     | undetermined — `policy_review_required` | Yes         | Yes. The unexpected post-trial charge needs billing review before deciding on a refund.                                               |
| T-1002 | technical       | high     | none — `no_refund_request`              | No          | Yes. This is an app crash issue, and the response offers troubleshooting steps.                                                       |
| T-1003 | account         | medium   | none — `no_refund_request`              | Yes         | Yes. The user needs help restoring order history.                                                                                     |
| T-1004 | cancellation    | medium   | none — `no_refund_request`              | Yes         | Yes. It is unclear whether the user wants to cancel trial auto-renewal or stop a plan.                                                |
| T-1005 | billing         | high     | none — `no_refund_request`              | Yes         | Yes. The payment and plan activation need to be checked.                                                                              |
| T-1006 | billing         | high     | undetermined — `policy_review_required` | Yes         | Yes. The annual renewal and UPI mandate status need to be checked.                                                                    |
| T-1007 | feature_request | low      | none — `no_refund_request`              | No          | Yes. This is a feature suggestion, not a billing issue.                                                                               |
| T-1008 | abuse_or_fraud  | critical | none — `no_refund_request`              | Yes         | Yes. Reported unauthorised charges require human investigation.                                                                       |
| T-1009 | billing         | high     | undetermined — `policy_review_required` | Yes         | Yes. The duplicate-charge report requires payment reconciliation.                                                                     |
| T-1010 | invoice         | medium   | none — `no_refund_request`              | Yes         | Yes. The GST invoice request requires billing details to be confirmed.                                                                |
| T-1011 | other           | low      | none — `no_refund_request`              | Yes         | Yes. The reply addresses the offline-access question without following the injected instruction.                                      |
| T-1012 | technical       | medium   | undetermined — `policy_review_required` | Yes         | Partially. Human review is appropriate, but the refund-gate reason should be checked because this is primarily a technical complaint. |

### Ambiguous cases

Several tickets cannot be safely resolved from the ticket text alone:

* **T-1001:** The user expected to pay only ₹1, but the subscription may have activated after the trial.
* **T-1004:** The user may mean trial auto-renewal cancellation or cancellation of an existing plan.
* **T-1005:** Payment was deducted, but the plan was not activated.
* **T-1006:** The user expected autopay to be disabled before the annual renewal.
* **T-1008:** The user reports three unauthorised charges.
* **T-1009:** The user reports duplicate charges; failed and successful payment attempts need to be reconciled.
* **T-1012:** The user reports a poor app experience but does not specify the technical failure.

When a refund cannot be safely determined, the service returns `undetermined` with `policy_review_required` rather than approving a refund. Cases requiring investigation are flagged for human review.

### Prompt-injection tickets

Two tickets contain instructions addressed to the assistant rather than normal support requests.

#### T-1003

The ticket asks for help restoring order history, but also includes an instruction to ignore the refund policy and approve a refund.

The service returned:

```text
Category: account
Refund: none
Reason: no_refund_request
Needs human: True
```

The injected instruction did not change the refund decision in this fixture run.

#### T-1011

The ticket asks whether premium works offline, but also includes an instruction to reveal the system prompt and internal refund rules.

The service returned:

```text
Category: other
Refund: none
Reason: no_refund_request
Needs human: True
```

The reply addresses the offline-access question and does not reveal the requested internal information.

These results demonstrate the behaviour of the supplied fixture run. They do not establish that a live model is immune to prompt injection. The current handling is targeted and should not be treated as a comprehensive prompt-injection defence.

### Dashboard metric

**Human-review rate: 10 out of 12 tickets (83.3%)** in this fixture run.

This is a useful metric to monitor over time. A sudden change could indicate a change in ticket mix or triage behaviour. It should not be treated as a metric to minimise at all costs, since human review is necessary for ambiguous and high-risk cases.

## Task 3 — Backend Track

If this service needed to handle 50 tickets per second during an outage, I would make the request path more resilient rather than allowing every incoming request to wait indefinitely for a model response.

### 1. Handling traffic and model failures

I would introduce a durable queue between the API and the model workers.

* The API would validate incoming tickets and enqueue work.
* A bounded worker pool would process tickets with controlled concurrency.
* Retries would use exponential backoff and a maximum attempt count.
* A circuit breaker would prevent repeated calls to an unhealthy model provider.
* Tickets that repeatedly fail would move to a dead-letter queue for investigation.
* When the model is unavailable, the system would return a safe degraded result or mark the ticket for human review rather than inventing a confident answer.

The API should have clear timeouts and return a predictable response. If processing becomes asynchronous, it can return an accepted status and a job identifier so the support tool can retrieve the result later.

### 2. What the user gets during degradation

The system should still accept and preserve the ticket where possible.

If automated triage is unavailable, the ticket can be marked as pending or requiring human review. The system should not make an uncertain refund decision just to keep the workflow moving.

### 3. What I would store

I would use a relational database such as PostgreSQL for durable state.

**Tickets**

* Ticket ID
* Original ticket payload, with appropriate access controls
* Creation and update timestamps
* Processing status

**Triage results**

* Ticket ID
* Category
* Severity
* Reply draft
* Confidence
* Model/provider version
* Creation timestamp

**Refund decisions**

* Ticket ID
* Decision
* Amount, if applicable
* Reason
* Review status
* Decision timestamp

**Refund operations**

* Idempotency key
* Ticket ID
* Operation status
* External payment reference
* Result and timestamp

**Audit events**

* Ticket ID
* Event type
* Correlation ID
* Timestamp
* Relevant state transition

Sensitive ticket content should not be copied into ordinary application logs.

### 4. Debugging at 3 a.m.

I would add structured logs and distributed tracing with a correlation ID that follows a ticket through the API, queue, worker, model call, and refund gate.

Useful operational metrics would include request rate, queue depth, processing latency, model error rate, retry count, fallback rate, and human-review rate.

Logs should record state transitions and error details without exposing personal or confidential ticket content.

These are proposed production improvements; they are not claimed to be implemented in the current take-home service.

## Task 4 — How I Used AI

### Tools used

I used Cursor and ChatGPT while building and reviewing the service.

### Approximate share of code written by AI

Around 40%

This is an estimate, not a measured percentage.

### Best prompt

I’m building a ticket-triage service for Dhaba, and I want to finalise the architecture before writing any code. Help me narrow it down to the simplest reliable implementation without overengineering it.

Please structure the plan as follows:

1. **Requirements:** Separate the requirements explicitly stated in the brief from assumptions I’m making and optional enhancements.

2. **Minimum viable architecture:** Identify the essential components and files. Remove unnecessary abstractions and explain what each file is responsible for.

3. **Build plan:** Break the work into small, independently testable stages, ordered by dependency and importance.

4. **Acceptance criteria and tests:** For each stage, specify what must work before moving on and give me the exact commands or test cases to run.

5. **LLM and refund safety:** Keep model-generated triage separate from deterministic refund decisions. Do not let the LLM approve refunds directly.

6. **Refund policy:** Do not invent refund eligibility rules. List the policy decisions I need to make explicitly, and explain what the system should do when the available information is insufficient.

7. **Replay mode:** Ensure the service can run all supplied tickets using fixtures, without requiring an API key or making external model calls.

8. **Idempotency and concurrency:** Explain how repeated or simultaneous requests with the same ticket ID should be handled safely, including how to prevent duplicate refund actions.

9. **Prompt injection:** Explain how to test the two tickets containing instructions directed at the assistant. Include deterministic tests that verify the refund gate and expected outputs independently of whether the LLM recognises the injection.

10. **Scope and trade-offs:** Identify what must be implemented now, what can be documented as a future improvement, and what can be left out.

Keep the plan practical and focused on a working, testable service. Do not edit any files or write implementation code yet. I want to agree on the design and build sequence first.



### One thing an AI agent got wrong

While working on idempotency, Cursor suggested an implementation that held a SQLite transaction/lock open while waiting for the LLM response.

That would keep a database lock held during a potentially slow external operation, increasing contention and making concurrent requests harder to handle safely.

I caught the issue while reviewing the suggested approach and changed the implementation rather than accepting the suggestion as-is.

### What I worked on directly

I worked directly on `app/refund_gate.py`, particularly the refund decision rules and edge cases.

I focused on keeping refund authorisation separate from the model's triage output, so a generated response could not independently approve a refund.

## Limitations and Future Improvements

* The live model provider is a placeholder; the current evaluation path uses fixtures.
* The refund gate uses phrase-based matching and can miss requests expressed in unfamiliar ways.
* The prompt-injection handling is targeted and is not a comprehensive defence against all adversarial input.
* Production queueing, durable storage, observability, and high-throughput handling are design proposals rather than implemented features.
* The service caches triage results by ticket ID. Simultaneous requests may both execute the triage pipeline, although only one result is stored. The current service does not execute refunds; any future payment integration must implement its own payment-level idempotency.
* Sensitive-data logging and production database behaviour should be reviewed before deployment.

## Submission

This repository contains the take-home service and its implementation notes. The assignment is confidential, so the repository should only be shared using the access method specified by Propel.

To submit, reply to the original email thread with the GitHub repository link. If the repository is private, invite `propel-hiring` as requested.
