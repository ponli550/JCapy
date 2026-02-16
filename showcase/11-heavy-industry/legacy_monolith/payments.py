# LEGACY PAYMENT SIMULATION
# Copyright (c) 2016 - DO NOT TOUCH WITHOUT APPROVAL
# Author: Dave (no longer with company)

import datetime
from decimal import Decimal

# MOCK ORM
class Model:
    def save(self): pass

class PaymentTransaction(Model):
    """
    Core payment table.
    WARNING: 'status' column assumes 'S' is success, 'F' is fail, 'P' is pending.
    Legacy note: 'amt' is a float, DO NOT CHANGE TO DECIMAL without migration.
    """
    def __init__(self, user_id, amount, currency='USD'):
        self.user_id = user_id
        self.amount = float(amount) # <--- DANGEROUS FLOAT
        self.currency = currency
        self.status = 'P'
        self.created_at = datetime.datetime.now()
        self.fraud_score = 0

def calculate_fraud_risk(user, amount):
    """
    biz_logic_v1: simple threshold
    """
    risk = 0
    if amount > 10000:
        risk += 50
    if user.country == 'XX': # Embargoed?
        risk += 100
    return risk

def process_payment(user, amount, gateway):
    """
    God function for payments.
    Follows 'Optimistic Locking' but mostly prays.
    """
    print(f"Processing {amount} via {gateway}...")

    # 1. Validation
    if amount <= 0:
        raise ValueError("Negative payment??")

    # 2. Fraud Check
    risk = calculate_fraud_risk(user, amount)
    if risk > 80:
        print("BLOCKED: High Fraud Risk")
        return False

    # 3. Gateway Call (Synchronous - blocks thread!)
    # TODO: Move to Celery (Ticket #402 from 2018)
    import time
    time.sleep(1.5) # Simulating slow bank API

    # 4. Save
    tx = PaymentTransaction(user.id, amount)
    tx.status = 'S'
    tx.save()

    print("SUCCESS: Payment recorded.")
    return True
