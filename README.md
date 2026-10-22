# SampleScope

[Application](https://github.com/gqzy999/corerelay-genlayer) · [Contract source](contracts/sample_scope.py) · [Finalized transactions](evidence/studionet.json)

A GenLayer contract primitive for purpose-bound geological sample use. A research request binds a sample reference, research plan, requester and supported official policy URL. Those inputs cannot be edited after registration. Policy applicability must be established for the sample reference; otherwise the model is instructed to mark every gate REVIEW. The sample reference itself remains a requester claim.

## Why consensus is needed

Published policies describe permissions, approval requirements and return/reporting obligations in prose. The leader reads the policy and extracts four evidence-backed decisions: purpose, destructive analysis, onward transfer, and return/reporting. Validators independently retrieve the same page and rerun the assessment. They compare all four decision fields and the policy hash, and verify that the leader quotations occur in their independently retrieved source. Free-form quotations are not required to be identical across model outputs.

Missing permission is REVIEW, never implied consent. DENY dominates REVIEW. A machine result never substitutes for an allocation decision. No sample shipment or physical enforcement is performed by this contract.

## State machine

`REGISTERED → WITHIN_SCOPE | CURATOR_REVIEW | BLOCKED`

`WITHIN_SCOPE | CURATOR_REVIEW → AUTHORIZED | DECLINED`

`AUTHORIZED → CLOSED`

Only the requester can assess its request. Only the deployer (deployment curator) can authorize, decline, or close. BLOCKED requests cannot be overridden; create a new corrected request. Notes and actors are retained in append-only per-request history. Authorization identifies the deployment operator, not a verified IODP official.

## Methods

| Method | Arguments | Access |
| --- | --- | --- |
| register | key, sample, source_url, plan | Any caller; caller becomes requester |
| assess | key | Requester; REGISTERED only |
| decide | key, approve:boolean, note | Curator; eligible assessed requests |
| close | key, note | Curator; AUTHORIZED only |
| get_request | key | Public read; JSON string |
| get_curator | none | Public read; address string |

## Deploy

1. Open https://studio.genlayer.com/ and select stable Studionet (61999).
2. Load `contracts/sample_scope.py` into the editor.
3. Deploy from the wallet that will act as the curator; constructor has no arguments.
4. Record the address and deployment transaction hash.
5. Use `get_curator` to verify the deployment operator before application use.
6. Paste the address into the app; complete register, assess, decide, close and readback.

The official GenVM linter has validated the pinned runner, storage types and ABI schema (`contracts/sample_scope.abi.json`). Ten tests also pass with the official GenLayer direct runner and real SDK/storage while external web/model I/O is mocked. These checks do not execute Wasm or live network consensus. A live Studionet deployment and complete finalized lifecycle are recorded in `evidence/studionet.json`. The example uses a dedicated test curator and an illustrative sample; it is not institutional authorization. Browser wallet signing is separate from the SDK-based test.

## Tests

Requires Python 3.12+. The lightweight unit tests need no additional dependencies. Run the official runner in a separate process to keep the lightweight SDK stub isolated.

```sh
python -m unittest discover -s tests -v
```

For the official SDK/storage tests and semantic checks:

```sh
python -m pip install -r requirements-dev.txt
genvm-lint check contracts/sample_scope.py
python scripts/prepare-test-sdk.py
python -m pytest tests_direct -q
```

The direct runner is pinned to the `v0.3.0-rc7` artifact containing the contract’s exact dependency hash. `scripts/prepare-test-sdk.py` obtains the pinned official artifact through the linter and shares it with the direct runner; run it once before the SDK tests. The four policies in `fixtures/scope_cases.json` are explicitly synthetic test data; passing fixtures is not evidence of live model accuracy.

The 19 lightweight tests execute the actual contract methods against a minimal mocked runtime boundary. They check access control, replay guards, malformed policy evidence, a forged leader quotation, terminal states, and the 81 combinations of the four gate statuses. They do not prove GenVM compatibility, model accuracy, live network availability, or consensus performance.

## Sources and boundaries

- https://publications.iodp.org/scientific_prospectus/353/353sp_10.htm
- https://www.iodp.org/resources/access-data-and-samples
- https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle

Supported sources are HTTPS pages under `publications.iodp.org` plus four fixed official policy pages listed in `POLICY_PAGES`. The default is `https://www.iodp.org/resources/access-data-and-samples`; publication pages may reject automated retrieval. An unavailable source aborts assessment without advancing the request. The allowlist establishes the source domain, not the policy's applicability to an individual sample. Public expedition pages may omit relevant conditions or point to additional policies. Missing or ambiguous information requires curator review. The content hash binds the text used during assessment; the original page is not archived. Changing pages may prevent validators from reaching agreement. Registration stores unverified user claims, not repository ownership evidence. Do not submit personal, sensitive, proprietary, biological, or regulated sample data. This is an independent research workflow with no IODP affiliation.
