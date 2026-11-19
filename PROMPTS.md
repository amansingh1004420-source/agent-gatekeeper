# PROMPTS.md

Project: Agent Gatekeeper for Amazon (online store)
Enrolment No: PGD202570947
Coding tool: Google Antigravity (model: Gemini 3.8 Flash)

## Main instructions I gave the coding agent

### Prompt 1 (15 Nov 2026): rules and decision logic

```
I am building a small Python prototype called "Agent Gatekeeper" for Amazon (online store). It decides whether a request from a customer's AI agent is ALLOW, ASK CUSTOMER or BLOCK.

Please do only these two things for now:

1. Create RULES.md with these 7 rules, checked in this order (first match wins):
R1: Agent not registered (unknown) -> BLOCK
R2: Agent is revoked -> BLOCK
R3: Action is "view order" -> ALLOW
R4: Action is "place order" or "return" and amount <= 5000 INR -> ALLOW
R5: Action is "place order" or "return" and amount > 5000 INR -> ASK CUSTOMER
R6: Action is "refund" (any amount) -> ASK CUSTOMER
R7: Anything else (unknown action) -> BLOCK

2. Create gatekeeper.py with a function decide(agent_name, action, amount, agents) that returns the decision, the rule number and a short reason. Use plain Python with no extra libraries, and add simple comments so a beginner can understand it.

Do not build a screen or audit log yet.
```

### Prompt 2 (17 Nov 2026): audit log

```
Now add an audit log to gatekeeper.py. Only do this one thing.

1. Create a function log_decision(agent_name, action, amount, decision, rule, reason) that appends one row to a file called audit_log.csv.
2. Each row must have these columns: date_time, agent_name, action, amount, decision, rule, reason.
3. date_time should be the current local date and time in the format YYYY-MM-DD HH:MM:SS.
4. If audit_log.csv does not exist yet, create it with the header row first.
5. Call log_decision automatically every time decide() returns a decision, including in the existing test cases at the bottom of the file.
6. Use only Python standard libraries (csv, datetime, os) and add simple comments so a beginner can understand it.

Do not run any commands yourself. I will run the file myself. Do not build a screen or the register/revoke feature yet.
```

### Prompt 3 (18 Nov 2026): register and revoke

```
Now add register and revoke features to gatekeeper.py. Only do this one thing.

1. Store agents in a file called agents.json. Each agent has: name, status ("active" or "revoked"), registered_at, revoked_at (empty if not revoked).
2. Create register_agent(agent_name) that adds a new agent with status "active" and registered_at set to the current local date and time (format YYYY-MM-DD HH:MM:SS). If the agent already exists, do not add it again.
3. Create revoke_agent(agent_name) that sets status to "revoked" and saves revoked_at with the current local date and time. If the agent does not exist, show a clear message.
4. Create load_agents() and save_agents(agents) to read and write agents.json. If agents.json does not exist, create it with two sample agents: alexa_shopper (active) and compromised_bot (revoked, with a revoked_at date and time).
5. Change decide() so it loads agents from agents.json. Keep rules R1 to R7 exactly as they are. Revoked agents must still be blocked by R2.
6. Write registering and revoking actions to audit_log.csv too (use decision values "REGISTER" and "REVOKE", rule "-").
7. In the test section at the bottom, add a short demo: register a new agent "test_agent", make one request that is allowed, revoke it, then make the same request again to show it is now blocked by R2.
8. Use only Python standard libraries (json, csv, datetime, os) and add simple comments so a beginner can understand it.

Do not run any commands yourself. I will run the file myself. Do not build a screen yet.
```

### Prompt 4 (18 Nov 2026): customer field, menu and enrolment number

```
Now add a simple interactive menu to gatekeeper.py so I can use it myself. Only do this one thing.

1. Add a "customer" field to every request. Change decide() to accept (customer, agent_name, action, amount) and add a "customer" column to audit_log.csv (update the header and every row written). Keep rules R1 to R7 exactly as they are. Update the existing test cases and demo so they still work with the customer field.
2. When I run "python gatekeeper.py", it should first print this header on the main screen:
   Agent Gatekeeper - Amazon
   Enrolment No: PGD202570947
3. Then show a text menu in a loop:
   1. Send a request (ask me for customer name, agent name, action, amount, then print the decision, rule number and reason)
   2. Register an agent
   3. Revoke an agent
   4. Show all agents (name, status, registered_at, revoked_at)
   5. Show last 10 audit log entries
   6. Run the built-in test cases
   7. Exit
4. Handle wrong input safely (for example a non-number amount) without crashing.
5. Use only Python standard libraries and add simple comments so a beginner can understand it.

Do not run any commands yourself. I will run the file myself. Do not build a web page.
```

## What I checked or changed myself

1. After every prompt I ran `python gatekeeper.py` myself in Anaconda Prompt, because I told the agent not to run commands. Python was not found in the normal Command Prompt, so I used Anaconda Prompt, where Python 3.13.9 works.
2. I ran the 6 test cases myself from the menu. In my first try of Test 1 I typed "view prder" by mistake and the gatekeeper correctly gave BLOCK (R7, unknown action). I noticed the typo, understood why R7 fired, and ran the test again with "view order" to get ALLOW (R3).
3. In Test 6 I entered the answers in the wrong order, so the agent name became "Aman" and the result was BLOCK (R1). I noticed it, understood why, and repeated the refund test correctly (ASK CUSTOMER, R6).
4. I picked my own sixth test case (a refund of Rs. 500) because refunds move the company's money to the customer, so I wanted to check that even a small refund goes to the customer for confirmation.
