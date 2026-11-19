"""
Agent Gatekeeper
================
An interactive prototype that evaluates requests from customer AI agents
and decides whether an action is ALLOW, ASK CUSTOMER, or BLOCK.

Features:
- Rules R1 to R7 for evaluation decisions
- Customer identification on every request
- Audit logging to audit_log.csv (including customer column)
- Agent registry management (load, save, register, revoke) in agents.json
- Interactive command-line menu
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


def log_decision(customer, agent_name, action, amount, decision, rule, reason):
    """
    Appends one record to audit_log.csv.
    If the file does not exist yet, creates it and writes the header row first.

    Parameters:
        customer (str): Name or ID of the customer.
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

        # Write CSV header row if the file is newly created
        if not file_exists:
            writer.writerow([
                "date_time",
                "customer",
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
            customer,
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
        customer="system",
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
        customer="system",
        agent_name=agent_name,
        action="revoke",
        amount=0,
        decision="REVOKE",
        rule="-",
        reason="Agent revoked"
    )

    return agents[agent_name]


def decide(customer, agent_name, action, amount=0, agents=None):
    """
    Decides whether an agent's request is allowed, blocked, or requires customer confirmation.
    Loads agents from agents.json if not provided.
    Automatically logs every decision to audit_log.csv before returning.

    Parameters:
        customer (str): Name or identifier of the customer.
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
    log_decision(customer, agent_name, action, amount, decision, rule, reason)

    return decision, rule, reason


def show_all_agents():
    """
    Displays all registered agents with their name, status, registered_at, and revoked_at.
    """
    agents = load_agents()
    if not agents:
        print("\n[INFO] No agents found in registry.")
        return

    print("\n" + "=" * 80)
    print("                           ALL REGISTERED AGENTS")
    print("=" * 80)
    print(f"{'Name':<20} | {'Status':<10} | {'Registered At':<20} | {'Revoked At':<20}")
    print("-" * 80)
    for name, data in agents.items():
        status = data.get("status", "unknown")
        registered_at = data.get("registered_at") or "-"
        revoked_at = data.get("revoked_at") or "-"
        print(f"{name:<20} | {status:<10} | {registered_at:<20} | {revoked_at:<20}")
    print("=" * 80)


def show_last_audit_logs(count=10):
    """
    Reads audit_log.csv and displays the most recent entries.

    Parameters:
        count (int): Number of recent entries to show (default: 10).
    """
    if not os.path.exists(AUDIT_LOG_FILE):
        print("\n[INFO] No audit log file found yet.")
        return

    with open(AUDIT_LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    # Check if there are data rows beyond the header
    if len(rows) <= 1:
        print("\n[INFO] Audit log is currently empty.")
        return

    # Extract the last 'count' rows
    data_rows = rows[1:]
    last_entries = data_rows[-count:]

    print("\n" + "=" * 115)
    print(f"                               LAST {len(last_entries)} AUDIT LOG ENTRIES")
    print("=" * 115)
    print(f"{'Date/Time':<20} | {'Customer':<12} | {'Agent':<16} | {'Action':<13} | {'Amount':<7} | {'Decision':<13} | {'Rule':<4} | Reason")
    print("-" * 115)

    for row in last_entries:
        # Safely read columns even if an older row had fewer fields
        d_time = row[0] if len(row) > 0 else "-"
        cust = row[1] if len(row) > 1 else "-"
        agent = row[2] if len(row) > 2 else "-"
        act = row[3] if len(row) > 3 else "-"
        amt = row[4] if len(row) > 4 else "0"
        dec = row[5] if len(row) > 5 else "-"
        rle = row[6] if len(row) > 6 else "-"
        rsn = row[7] if len(row) > 7 else "-"
        print(f"{d_time:<20} | {cust:<12} | {agent:<16} | {act:<13} | {amt:<7} | {dec:<13} | {rle:<4} | {rsn}")

    print("=" * 115)


def run_tests():
    """
    Runs the built-in test suite covering rules R1 to R7 and the register/revoke lifecycle.
    """
    # Ensure fresh state for test_agent if re-running test suite
    existing_agents = load_agents()
    if "test_agent" in existing_agents:
        del existing_agents["test_agent"]
        save_agents(existing_agents)

    # 1. Standard rule tests covering R1 to R7
    print("\n=== Running Standard Gatekeeper Tests (R1 to R7) ===")
    test_cases = [
        ("Alice", "unknown_agent", "view order", 0),          # R1: Unknown agent -> BLOCK
        ("Bob", "compromised_bot", "view order", 0),          # R2: Revoked agent -> BLOCK
        ("Charlie", "alexa_shopper", "view order", 0),        # R3: View order -> ALLOW
        ("David", "alexa_shopper", "place order", 2500),      # R4: Place order <= 5000 -> ALLOW
        ("Emma", "alexa_shopper", "return", 5000),            # R4: Return <= 5000 -> ALLOW
        ("Frank", "alexa_shopper", "place order", 12000),     # R5: Place order > 5000 -> ASK CUSTOMER
        ("Grace", "alexa_shopper", "refund", 500),            # R6: Refund -> ASK CUSTOMER
        ("Heidi", "alexa_shopper", "delete account", 0),      # R7: Unknown action -> BLOCK
    ]

    for customer, agent, action, amt in test_cases:
        decision, rule, reason = decide(customer, agent, action, amt)
        print(f"[{rule}] {decision:<12} | Customer: {customer:<8} | Agent: {agent:<16} | Action: {action:<14} | Amt: {amt:<5} | Reason: {reason}")

    # 2. Demo: Register -> Allow -> Revoke -> Block by R2
    print("\n=== Demo: Register and Revoke Lifecycle ===")

    # Step A: Register test_agent
    print("1. Registering 'test_agent'...")
    register_agent("test_agent")

    # Step B: Make a request that is allowed while active
    print("\n2. Making request while active (view order):")
    decision, rule, reason = decide("DemoCustomer", "test_agent", "view order", 0)
    print(f"   [{rule}] {decision:<12} | Reason: {reason}")

    # Step C: Revoke test_agent
    print("\n3. Revoking 'test_agent'...")
    revoke_agent("test_agent")

    # Step D: Make the same request again (should now be blocked by R2)
    print("\n4. Making same request after revocation (view order):")
    decision, rule, reason = decide("DemoCustomer", "test_agent", "view order", 0)
    print(f"   [{rule}] {decision:<12} | Reason: {reason}")

    print("\nAll decisions, registrations, and revocations have been logged to audit_log.csv.")


def main_menu():
    """
    Displays the interactive text menu and handles user choices safely in a loop.
    """
    # Print the required startup header
    print("Agent Gatekeeper - Amazon")
    print("Enrolment No: PGD202570947")

    while True:
        print("\n" + "=" * 45)
        print("                  MAIN MENU")
        print("=" * 45)
        print("1. Send a request")
        print("2. Register an agent")
        print("3. Revoke an agent")
        print("4. Show all agents (name, status, registered_at, revoked_at)")
        print("5. Show last 10 audit log entries")
        print("6. Run the built-in test cases")
        print("7. Exit")
        print("=" * 45)

        try:
            choice = input("Enter your choice (1-7): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Agent Gatekeeper. Goodbye!")
            break

        # Option 1: Send a request
        if choice == "1":
            print("\n--- Send a Request ---")
            try:
                customer = input("Enter customer name: ").strip()
                if not customer:
                    customer = "Unknown Customer"

                agent_name = input("Enter agent name: ").strip()
                if not agent_name:
                    print("[ERROR] Agent name cannot be empty.")
                    continue

                action = input("Enter action (e.g., view order, place order, return, refund): ").strip()
                if not action:
                    print("[ERROR] Action cannot be empty.")
                    continue

                amount_input = input("Enter amount in INR (e.g., 2500 or 0): ").strip()
                # Safely convert amount to float, handling invalid input
                try:
                    amount = float(amount_input) if amount_input else 0.0
                    if amount < 0:
                        print("[WARNING] Negative amount entered. Defaulting to 0.")
                        amount = 0.0
                except ValueError:
                    print("[ERROR] Invalid amount! Please enter a valid number (e.g., 500, 2500.50).")
                    continue

                # Run decision
                decision, rule, reason = decide(customer, agent_name, action, amount)

                print("\n" + "-" * 40)
                print("               DECISION")
                print("-" * 40)
                print(f"Customer:    {customer}")
                print(f"Agent Name:  {agent_name}")
                print(f"Action:      {action}")
                print(f"Amount:      {amount} INR")
                print(f"Decision:    {decision}")
                print(f"Rule Number: {rule}")
                print(f"Reason:      {reason}")
                print("-" * 40)

            except (KeyboardInterrupt, EOFError):
                print("\nRequest cancelled.")
                continue

        # Option 2: Register an agent
        elif choice == "2":
            print("\n--- Register an Agent ---")
            try:
                agent_name = input("Enter agent name to register: ").strip()
                if not agent_name:
                    print("[ERROR] Agent name cannot be empty.")
                    continue
                register_agent(agent_name)
            except (KeyboardInterrupt, EOFError):
                print("\nRegistration cancelled.")
                continue

        # Option 3: Revoke an agent
        elif choice == "3":
            print("\n--- Revoke an Agent ---")
            try:
                agent_name = input("Enter agent name to revoke: ").strip()
                if not agent_name:
                    print("[ERROR] Agent name cannot be empty.")
                    continue
                revoke_agent(agent_name)
            except (KeyboardInterrupt, EOFError):
                print("\nRevocation cancelled.")
                continue

        # Option 4: Show all agents
        elif choice == "4":
            show_all_agents()

        # Option 5: Show last 10 audit log entries
        elif choice == "5":
            show_last_audit_logs(10)

        # Option 6: Run built-in test cases
        elif choice == "6":
            run_tests()

        # Option 7: Exit
        elif choice == "7":
            print("\nExiting Agent Gatekeeper. Goodbye!")
            break

        # Invalid menu selection
        else:
            print("\n[ERROR] Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main_menu()
