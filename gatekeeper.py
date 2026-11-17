"""
Agent Gatekeeper
================
A small prototype that evaluates requests from customer AI agents
and decides whether an action is ALLOW, ASK CUSTOMER, or BLOCK.
Also logs every evaluated decision to an audit log CSV file.
"""

import csv
from datetime import datetime
import os


def log_decision(agent_name, action, amount, decision, rule, reason):
    """
    Appends one decision record to the audit_log.csv file.
    If the file does not exist yet, creates it and writes the header row first.

    Parameters:
        agent_name (str): Name or identifier of the AI agent.
        action (str): The requested action.
        amount (int or float): The transaction amount in INR.
        decision (str): "ALLOW", "ASK CUSTOMER", or "BLOCK".
        rule (str): The rule that triggered (e.g., "R1" to "R7").
        reason (str): A short explanation of the decision.
    """
    log_filename = "audit_log.csv"

    # Check whether the audit log file already exists
    file_exists = os.path.exists(log_filename)

    # Get the current local date and time in YYYY-MM-DD HH:MM:SS format
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Open the CSV file in append mode ('a') so new entries are added at the end
    with open(log_filename, mode="a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # If the file is newly created, write the header row first
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

        # Append the new decision row
        writer.writerow([
            date_time,
            agent_name,
            action,
            amount,
            decision,
            rule,
            reason
        ])


def decide(agent_name, action, amount, agents):
    """
    Decides whether an agent's request is allowed, blocked, or requires customer confirmation.
    Automatically logs every decision to audit_log.csv before returning.

    Parameters:
        agent_name (str): Name or identifier of the AI agent.
        action (str): The requested action (e.g., 'view order', 'place order', 'return', 'refund').
        amount (int or float): The transaction amount in INR (can be 0 or None if not applicable).
        agents (dict): Known agents database, mapping an agent name to its status
                       (e.g., {"shopping_bot": "active", "old_bot": "revoked"}).

    Returns:
        tuple: (decision, rule_number, reason)
            - decision (str): "ALLOW", "ASK CUSTOMER", or "BLOCK"
            - rule_number (str): The rule that triggered (e.g., "R1" through "R7")
            - reason (str): A short explanation of the decision
    """
    # Normalize action text to lowercase and remove leading/trailing spaces for clean comparisons
    clean_action = action.strip().lower() if isinstance(action, str) else ""

    # Ensure amount is a valid number for comparison (default to 0 if None)
    clean_amount = amount if amount is not None else 0

    # -------------------------------------------------------------
    # R1: Check if the agent is registered
    # -------------------------------------------------------------
    if agent_name not in agents:
        decision, rule, reason = "BLOCK", "R1", "Agent not registered (unknown)"

    else:
        agent_record = agents[agent_name]

        # Check status if the record is a dictionary or a plain string
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

    # Automatically log the decision to audit_log.csv
    log_decision(agent_name, action, amount, decision, rule, reason)

    return decision, rule, reason


# Quick demonstration of all 7 rules when run directly
if __name__ == "__main__":
    # Sample agents registry
    agents_db = {
        "alexa_shopper": "active",
        "compromised_bot": "revoked",
        "custom_agent": {"status": "active"},
    }

    # Test cases covering R1 to R7
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

    print("--- Running Agent Gatekeeper Tests ---")
    for agent, action, amt in test_cases:
        decision, rule, reason = decide(agent, action, amt, agents_db)
        print(f"[{rule}] {decision:<12} | Agent: {agent:<15} | Action: {action:<14} | Amt: {amt:<5} | Reason: {reason}")

    print("\nAll decisions have been logged to audit_log.csv.")
