"""
Agent Gatekeeper
================
A prototype that evaluates requests from customer AI agents
and decides whether an action is ALLOW, ASK CUSTOMER, or BLOCK.

Features:
- Rules R1 to R7 for evaluation decisions
- Audit logging to audit_log.csv
- Agent registry management (load, save, register, revoke) in agents.json
"""

import csv
from datetime import datetime
import json
import os

# Filenames used for data persistence
AGENTS_FILE = "agents.json"
AUDIT_LOG_FILE = "audit_log.csv"


def load_agents():
    """
    Loads all registered agents from agents.json.
    If agents.json does not exist yet, creates it with two sample agents:
      - alexa_shopper (active)
      - compromised_bot (revoked)

    Returns:
        dict: A dictionary of agents, keyed by agent name.
    """
    if not os.path.exists(AGENTS_FILE):
        # Default sample agents created on first run
        sample_agents = {
            "alexa_shopper": {
                "name": "alexa_shopper",
                "status": "active",
                "registered_at": "2026-11-15 10:00:00",
                "revoked_at": ""
            },
            "compromised_bot": {
                "name": "compromised_bot",
                "status": "revoked",
                "registered_at": "2026-11-15 09:00:00",
                "revoked_at": "2026-11-15 10:30:00"
            }
        }
        save_agents(sample_agents)
        return sample_agents

    # Read and parse existing agents.json
    with open(AGENTS_FILE, mode="r", encoding="utf-8") as f:
        return json.load(f)


def save_agents(agents):
    """
    Saves the agents dictionary to agents.json with clean formatting.

    Parameters:
        agents (dict): Dictionary of agents to save.
    """
    with open(AGENTS_FILE, mode="w", encoding="utf-8") as f:
        json.dump(agents, f, indent=4)


def log_decision(agent_name, action, amount, decision, rule, reason):
    """
    Appends one record to audit_log.csv.
    If the file does not exist yet, creates it and writes the header row first.

    Parameters:
        agent_name (str): Name or identifier of the AI agent.
        action (str): The requested action (or 'register' / 'revoke').
        amount (int or float): The transaction amount in INR (0 if not applicable).
        decision (str): "ALLOW", "ASK CUSTOMER", "BLOCK", "REGISTER", or "REVOKE".
        rule (str): The rule identifier (e.g., "R1" to "R7", or "-" for admin actions).
        reason (str): A short explanation of the decision or action.
    """
    file_exists = os.path.exists(AUDIT_LOG_FILE)

    # Current local date and time in YYYY-MM-DD HH:MM:SS format
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(AUDIT_LOG_FILE, mode="a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # Write CSV header row if the file is new
        if not file_exists:
            writer.writerow([
                "date_time",
                "agent_name",
                "action",
                "amount",
                "decision",
                "rule",
                "reason"
            ])

        # Write data row
        writer.writerow([
            date_time,
            agent_name,
            action,
            amount,
            decision,
            rule,
            reason
        ])


def register_agent(agent_name):
    """
    Registers a new agent with status 'active'.
    If the agent already exists, it is not added again.
    Logs the registration to audit_log.csv.

    Parameters:
        agent_name (str): The unique name of the agent to register.

    Returns:
        dict: The agent data dictionary.
    """
    agents = load_agents()

    # Do not add again if already registered
    if agent_name in agents:
        print(f"[REGISTER] Agent '{agent_name}' already exists. Skipping registration.")
        return agents[agent_name]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_agent = {
        "name": agent_name,
        "status": "active",
        "registered_at": now,
        "revoked_at": ""
    }

    # Save to agents.json
    agents[agent_name] = new_agent
    save_agents(agents)
    print(f"[REGISTER] Agent '{agent_name}' registered successfully.")

    # Log to audit_log.csv
    log_decision(
        agent_name=agent_name,
        action="register",
        amount=0,
        decision="REGISTER",
        rule="-",
        reason="Agent registered"
    )

    return new_agent


def revoke_agent(agent_name):
    """
    Revokes an agent's access by updating its status to 'revoked'
    and recording the revoked_at timestamp.
    If the agent does not exist, displays a clear message.
    Logs the revocation to audit_log.csv.

    Parameters:
        agent_name (str): The name of the agent to revoke.

    Returns:
        dict or None: The updated agent data, or None if agent not found.
    """
    agents = load_agents()

    # Show clear message if agent not found
    if agent_name not in agents:
        print(f"[REVOKE] Cannot revoke: Agent '{agent_name}' does not exist.")
        return None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agents[agent_name]["status"] = "revoked"
    agents[agent_name]["revoked_at"] = now

    # Save to agents.json
    save_agents(agents)
    print(f"[REVOKE] Agent '{agent_name}' revoked successfully.")

    # Log to audit_log.csv
    log_decision(
        agent_name=agent_name,
        action="revoke",
        amount=0,
        decision="REVOKE",
        rule="-",
        reason="Agent revoked"
    )

    return agents[agent_name]


def decide(agent_name, action, amount=0, agents=None):
    """
    Decides whether an agent's request is allowed, blocked, or requires customer confirmation.
    Loads agents from agents.json if not provided.
    Automatically logs every decision to audit_log.csv before returning.

    Parameters:
        agent_name (str): Name or identifier of the AI agent.
        action (str): The requested action (e.g., 'view order', 'place order', 'return', 'refund').
        amount (int or float): The transaction amount in INR (defaults to 0 if not applicable).
        agents (dict, optional): Known agents database. If None, loaded from agents.json.

    Returns:
        tuple: (decision, rule_number, reason)
            - decision (str): "ALLOW", "ASK CUSTOMER", or "BLOCK"
            - rule_number (str): The rule that triggered (e.g., "R1" through "R7")
            - reason (str): A short explanation of the decision
    """
    # Load agents from agents.json if not explicitly provided
    if agents is None:
        agents = load_agents()

    # Normalize action text to lowercase and remove spaces for safe comparison
    clean_action = action.strip().lower() if isinstance(action, str) else ""

    # Ensure amount is numeric (default to 0 if None)
    clean_amount = amount if amount is not None else 0

    # -------------------------------------------------------------
    # R1: Check if the agent is registered
    # -------------------------------------------------------------
    if agent_name not in agents:
        decision, rule, reason = "BLOCK", "R1", "Agent not registered (unknown)"

    else:
        agent_record = agents[agent_name]

        # Extract status whether stored as a dict or plain string
        if isinstance(agent_record, dict):
            agent_status = agent_record.get("status", "").lower()
        else:
            agent_status = str(agent_record).lower()

        # ---------------------------------------------------------
        # R2: Check if the agent is revoked
        # ---------------------------------------------------------
        if agent_status == "revoked":
            decision, rule, reason = "BLOCK", "R2", "Agent is revoked"

        # ---------------------------------------------------------
        # R3: Safe read-only action
        # ---------------------------------------------------------
        elif clean_action == "view order":
            decision, rule, reason = "ALLOW", "R3", "Action is 'view order'"

        # ---------------------------------------------------------
        # R4: Low-risk purchase or return (<= 5000 INR)
        # ---------------------------------------------------------
        elif clean_action in ("place order", "return") and clean_amount <= 5000:
            decision, rule, reason = "ALLOW", "R4", "Action is 'place order' or 'return' and amount <= 5000 INR"

        # ---------------------------------------------------------
        # R5: High-risk purchase or return (> 5000 INR)
        # ---------------------------------------------------------
        elif clean_action in ("place order", "return") and clean_amount > 5000:
            decision, rule, reason = "ASK CUSTOMER", "R5", "Action is 'place order' or 'return' and amount > 5000 INR"

        # ---------------------------------------------------------
        # R6: Any refund request
        # ---------------------------------------------------------
        elif clean_action == "refund":
            decision, rule, reason = "ASK CUSTOMER", "R6", "Action is 'refund' (any amount)"

        # ---------------------------------------------------------
        # R7: Anything else (unknown or unhandled action)
        # ---------------------------------------------------------
        else:
            decision, rule, reason = "BLOCK", "R7", "Unknown action"

    # Automatically log every decision to audit_log.csv
    log_decision(agent_name, action, amount, decision, rule, reason)

    return decision, rule, reason


# Demonstration of rules and register/revoke lifecycle when run directly
if __name__ == "__main__":
    # Ensure fresh state for test_agent if re-running test script
    existing_agents = load_agents()
    if "test_agent" in existing_agents:
        del existing_agents["test_agent"]
        save_agents(existing_agents)

    # 1. Standard rule tests covering R1 to R7
    print("=== Running Standard Gatekeeper Tests (R1 to R7) ===")
    test_cases = [
        ("unknown_agent", "view order", 0),          # R1: Unknown agent -> BLOCK
        ("compromised_bot", "view order", 0),       # R2: Revoked agent -> BLOCK
        ("alexa_shopper", "view order", 0),         # R3: View order -> ALLOW
        ("alexa_shopper", "place order", 2500),     # R4: Place order <= 5000 -> ALLOW
        ("alexa_shopper", "return", 5000),          # R4: Return <= 5000 -> ALLOW
        ("alexa_shopper", "place order", 12000),    # R5: Place order > 5000 -> ASK CUSTOMER
        ("alexa_shopper", "refund", 500),           # R6: Refund -> ASK CUSTOMER
        ("alexa_shopper", "delete account", 0),     # R7: Unknown action -> BLOCK
    ]

    for agent, action, amt in test_cases:
        decision, rule, reason = decide(agent, action, amt)
        print(f"[{rule}] {decision:<12} | Agent: {agent:<16} | Action: {action:<14} | Amt: {amt:<5} | Reason: {reason}")

    # 2. Demo: Register -> Allow -> Revoke -> Block by R2
    print("\n=== Demo: Register and Revoke Lifecycle ===")

    # Step A: Register test_agent
    print("1. Registering 'test_agent'...")
    register_agent("test_agent")

    # Step B: Make a request that is allowed while active
    print("\n2. Making request while active (view order):")
    decision, rule, reason = decide("test_agent", "view order", 0)
    print(f"   [{rule}] {decision:<12} | Reason: {reason}")

    # Step C: Revoke test_agent
    print("\n3. Revoking 'test_agent'...")
    revoke_agent("test_agent")

    # Step D: Make the same request again (should now be blocked by R2)
    print("\n4. Making same request after revocation (view order):")
    decision, rule, reason = decide("test_agent", "view order", 0)
    print(f"   [{rule}] {decision:<12} | Reason: {reason}")

    print("\nAll decisions, registrations, and revocations have been logged to audit_log.csv.")
