"""Built-in sample documents for one-click demos.

All people, companies, addresses and account numbers below are fictional
sample data written for demonstration purposes.
"""

SAMPLE_FREELANCE = """FREELANCE SERVICES AGREEMENT

This Freelance Services Agreement (the "Agreement") is made on October 1, 2026,
between:

Northwind Studio LLC, a company based at 400 Market Street, San Francisco, CA 94105,
represented by its Content Manager, Sarah Collins (sarah.collins@northwindstudio.example,
+1 415 555 0132) — the "Client";

and

Aarav Mehta, an independent content writer based at 14 Rosewood Lane, Pune,
Maharashtra 411001, India (aarav.mehta@example.com, +91 98110 24680) — the "Freelancer".

1. SERVICES
The Freelancer will write blog articles and social media posts for the Client's
website and channels, as assigned in writing by the Client from time to time.

2. FEES AND PAYMENT
The Client will pay the Freelancer a fee of $500 for each completed article package.
Payment is due within 30 days of delivery of each package. The Freelancer will send
an invoice by email after each delivery.
Payment will be made by bank transfer to the Freelancer's account:
Account holder: Aarav Mehta, Account No. 50100234567890, Bank: HDFC Bank,
IFSC: HDFC0001234.
If payment is late, interest of 2% per month applies to the overdue amount.

3. TERM AND RENEWAL
This Agreement starts on October 1, 2026 and runs for an initial term of 6 months.
After the initial term, it renews automatically month to month unless either party
gives at least 15 days' written notice of cancellation before the renewal date.

4. TERMINATION
Either party may terminate this Agreement during the initial term only for material
breach, after giving 15 days' written notice and a chance to fix the breach.

5. OTHER TERMS
The Freelancer keeps no ownership of the delivered articles once paid for; all
rights in the delivered work pass to the Client on payment. The Freelancer may
show the published work in his portfolio.
"""

SAMPLE_RENTAL = """RENTAL AGREEMENT

This Rental Agreement is made on October 15, 2026, between:

Priya Nair, residing at 9 Temple Road, Kochi, Kerala 682001
(priya.nair@example.com, +91 98450 77881) — the "Landlord";

and

Daniel Osei (daniel.osei@example.net, +44 7700 900123) — the "Tenant".

1. PROPERTY
The Landlord lets to the Tenant Flat 8B, Lakeview Residency, Whitefield,
Bengaluru, Karnataka 560066, for residential use only.

2. TERM
The tenancy starts on November 1, 2026 and lasts for a fixed term of 11 months,
ending on September 30, 2027. This Agreement does NOT renew automatically.
Any extension must be agreed in a new written agreement signed by both parties.

3. RENT AND DEPOSIT
The rent is Rs. 25,000 per month, payable in advance on or before the 5th day
of each month to the Landlord's bank account (Account No. 302198475610,
State Bank of India).
Before moving in, the Tenant will pay a refundable security deposit of
Rs. 50,000. The deposit will be returned within 30 days after the Tenant
vacates, less any lawful deductions for damage or unpaid bills.

4. TERMINATION AND NOTICE
Either party may end this Agreement early by giving at least 30 days' written
notice to the other party. The Tenant must leave the property in good condition
at the end of the tenancy.

5. OTHER TERMS
The Tenant may not sublet the property. One small pet is allowed. The Landlord
will arrange major repairs; the Tenant is responsible for day-to-day upkeep.
"""

SAMPLES = [
    {
        "id": "freelance",
        "title": "Freelance services agreement",
        "description": "A writer's contract with payment terms, bank details and automatic renewal.",
        "text": SAMPLE_FREELANCE,
    },
    {
        "id": "rental",
        "title": "Rental agreement",
        "description": "A flat rental with a fixed term, monthly rent and a security deposit — no auto-renewal.",
        "text": SAMPLE_RENTAL,
    },
]
