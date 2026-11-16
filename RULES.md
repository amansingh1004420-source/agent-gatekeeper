# Agent Gatekeeper - Decision Rules

The **Agent Gatekeeper** evaluates incoming requests from customer AI agents to an online store (Amazon) and decides whether each request should be:
- **ALLOW**: Automatically permitted to proceed.
- **ASK CUSTOMER**: Requires human confirmation from the customer before proceeding.
- **BLOCK**: Denied and not allowed to execute.

---

## Evaluation Order

Rules are evaluated sequentially from **R1 to R7**. **First match wins** — once a rule matches, its decision is returned immediately and subsequent rules are skipped.

| Rule | Condition | Decision | Description / Reason |
| :--- | :--- | :--- | :--- |
| **R1** | Agent not registered (unknown) | **BLOCK** | The agent is not found in the registered agents database. |
| **R2** | Agent is revoked | **BLOCK** | The agent was previously registered but has been revoked. |
| **R3** | Action is `"view order"` | **ALLOW** | Safe read-only action; allowed for any valid agent. |
| **R4** | Action is `"place order"` or `"return"` **and** `amount <= 5000 INR` | **ALLOW** | Low-risk transaction under or equal to the 5,000 INR safety threshold. |
| **R5** | Action is `"place order"` or `"return"` **and** `amount > 5000 INR` | **ASK CUSTOMER** | High-value transaction exceeding 5,000 INR; customer must approve. |
| **R6** | Action is `"refund"` (any amount) | **ASK CUSTOMER** | Financial disbursement/refund always requires explicit customer confirmation. |
| **R7** | Anything else (unknown action) | **BLOCK** | Default deny: any action not explicitly recognized is blocked. |
