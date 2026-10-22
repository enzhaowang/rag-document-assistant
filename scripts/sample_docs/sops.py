"""Standard operating procedures: returns, warranty claims, escalation and RMA."""

from scripts.sample_docs.model import (
    SampleDoc,
    bullets,
    fact,
    h1,
    h2,
    note,
    p,
    page_break,
    steps,
    table,
)

# ------------------------------------------------------------------- returns

RETURNS_AND_REFUNDS = SampleDoc(
    filename="SOP - Returns and Refunds.pdf",
    title="Returns and Refunds SOP",
    doc_type="sop",
    doc_number="LHS-SOP-CC-004",
    revision="2.3",
    effective_date="January 5, 2026",
    owner="Customer Care Operations",
    audience="Customer Care agents (Tier 1), Team Leads, Returns Processing Center",
    purpose=(
        "Defines how Customer Care handles return requests and refunds for products "
        "bought directly from Lumora (online store and phone orders), from eligibility "
        "checks to refund approval. Products bought from retail partners are returned "
        "through the retailer and are out of scope. Warranty replacements after the "
        "return window follow the Warranty Claims SOP (LHS-SOP-TS-007)."
    ),
    blocks=(
        h1("1. Definitions"),
        table(
            ("Term", "Definition"),
            [
                (
                    "Delivery date",
                    "The date the carrier marked the order as delivered in the "
                    "Order Management System (OMS).",
                ),
                (
                    "Change-of-mind return",
                    "A return of a working product the customer no longer wants.",
                ),
                (
                    "Defective return",
                    "A return within the return window of a product that "
                    "does not work as described, confirmed by troubleshooting.",
                ),
                (
                    "RPC",
                    "Returns Processing Center, the facility that receives, inspects "
                    "and grades returned units.",
                ),
                (
                    "RMA",
                    "Return Merchandise Authorization number, created in OMS for every "
                    "physical return (see LHS-SOP-OPS-011).",
                ),
                ("LumoraDesk", "The customer support ticketing system."),
            ],
            widths=(1.2, 3.8),
        ),
        h1("2. Return Eligibility"),
        h2("2.1 Return Window"),
        p(
            "Customers may return any product bought directly from Lumora within 30 "
            "calendar days of the delivery date, for any reason. The return window is "
            "counted from the delivery date shown in OMS, not from the order date. The "
            "return is considered on time if the RMA is created within the window; the "
            "customer then has 14 days to ship the item."
        ),
        p(
            "**Holiday extension.** Orders delivered between November 15 and December 31 "
            "can be returned until January 31 of the following year, or within the "
            "standard 30 days if that is later. The extension applies to change-of-mind "
            "and defective returns alike, but it does not apply to orders placed by "
            "business accounts or to orders containing more than five units of the same "
            "product. Agents must select the reason modifier HOL in OMS so that the "
            "return is not flagged as late by the automated window check."
        ),
        h2("2.2 Condition Requirements"),
        bullets(
            "The product must be complete, including the wall plate, trim plate, screws and "
            "any accessories that came in the box.",
            "Opened products are accepted. Customers should factory reset the device and "
            "remove it from their Lumora account before shipping.",
            "Products with physical damage, liquid damage or engraving are not accepted as "
            "change-of-mind returns.",
        ),
        h2("2.3 Non-Returnable Items"),
        bullets(
            'Items marked "Final Sale" on the order confirmation (clearance stock).',
            "Gift cards and Lumora Plus subscription fees (see the Billing FAQ for "
            "subscription cancellations).",
            "Professional installation services that have already been performed. The $129 "
            "installation fee is refunded in full only if the appointment has not yet "
            "taken place.",
            "Power Extender Kits (PEK-1) that have been installed in the equipment.",
        ),
        h2("2.4 Restocking Fee"),
        p(
            "A 15% restocking fee applies to opened change-of-mind returns when the RMA is "
            "created more than 14 days after delivery. No restocking fee is charged for "
            "unopened products, defective returns, wrong items shipped, or items damaged "
            "in transit. Team Leads may waive the fee once per customer per calendar year."
        ),
        page_break(),
        h1("3. Procedure: Creating a Return"),
        steps(
            "Verify the customer's identity using the order number plus the email address "
            "or the last four digits of the phone number on the order.",
            "Open the order in OMS and confirm the delivery date, the payment method and "
            "whether any item is marked Final Sale.",
            "Confirm eligibility against section 2. If the return window has passed, check "
            "whether the product is still under warranty and follow LHS-SOP-TS-007 "
            "instead.",
            "For a defective return, complete the troubleshooting steps for the product "
            "in the relevant product guide and record them in the LumoraDesk ticket.",
            "Select the return reason code (Table 3-1) and create an RMA of type RET in "
            "OMS as described in the RMA Process SOP.",
            "Confirm the refund amount, any restocking fee and how the refund will be "
            "paid. Read the amounts back to the customer.",
            "Send the prepaid return label from OMS. The label is emailed within 1 "
            "business day and is valid for 14 days.",
            "Link the RMA number to the LumoraDesk ticket and set the ticket to Pending - "
            "Return in Transit.",
        ),
        table(
            ("Code", "Reason", "Restocking fee", "Shipping refunded"),
            [
                ("CM-01", "Change of mind", "Possible (see 2.4)", "No"),
                ("DF-02", "Defective - confirmed by troubleshooting", "No", "Yes"),
                ("WI-03", "Wrong item shipped", "No", "Yes"),
                ("DT-04", "Damaged in transit (report within 7 days of delivery)", "No", "Yes"),
                ("MP-05", "Missing parts - replacement parts declined", "No", "Yes"),
            ],
            widths=(0.7, 2.6, 1.2, 1.2),
            caption="Table 3-1. Return reason codes.",
        ),
        h1("4. Refunds"),
        h2("4.1 Refund Approval Thresholds"),
        p(
            "The refund amount is the total paid for the returned items, including tax, "
            "less any restocking fee. Approval authority depends on the refund amount per "
            "order. Agents must not split a refund across several transactions to stay "
            "below a threshold."
        ),
        table(
            ("Refund amount per order", "Approver", "Notes"),
            [
                ("Up to $250.00", "Customer Care agent (Tier 1)", "Approve in OMS directly."),
                (
                    "$250.01 to $1,000.00",
                    "Team Lead",
                    "Approval request in OMS; Team Lead responds within 4 business hours.",
                ),
                (
                    "$1,000.01 to $5,000.00",
                    "Customer Care Manager",
                    "Attach order history and ticket summary.",
                ),
                (
                    "Above $5,000.00",
                    "Customer Care Manager and Finance Controller",
                    "Both approvals required before the refund is released.",
                ),
            ],
            widths=(1.4, 1.6, 2.2),
            caption="Table 4-1. Refund approval matrix.",
        ),
        h2("4.2 Refund Timing and Method"),
        p(
            "Refunds are issued within 5 business days after the RPC records a passed "
            "inspection. Refunds always go back to the original payment method. Card "
            "refunds can take an additional 3 to 10 business days to appear on the "
            "customer's statement, depending on the card issuer. Orders paid with a gift "
            "card or store credit are refunded as store credit, which is available "
            "immediately."
        ),
        h2("4.3 Shipping Charges"),
        p(
            "Original shipping charges are refunded only for reason codes DF-02, WI-03, "
            "DT-04 and MP-05. Return shipping is always free when the customer uses the "
            "prepaid label from OMS."
        ),
        h2("4.3.1 Expired or Closed Cards"),
        p(
            "If the original card has expired or been closed, the refund is still sent to "
            "that card; card issuers forward the credit to the replacement card or to the "
            "account. If the issuer rejects the refund, OMS converts it to store credit "
            "automatically and the agent should offer to reissue it by check, which takes "
            "up to 10 business days."
        ),
        h2("4.3.2 Partial Returns From Bundles"),
        p(
            "Items bought as a bundle (for example the T3 with one Room Sensor S1, SKU "
            "LT-T3-02) can be returned individually. The refund for each item is its share "
            "of the bundle price in proportion to the list prices, not the full list price "
            "of the item."
        ),
        page_break(),
        h2("4.4 Inspection Grades and Partial Refunds"),
        p(
            "The RPC grades every returned unit using the grading scale in the RMA Process "
            "SOP. The grade determines the refund outcome for change-of-mind returns:"
        ),
        table(
            ("Grade", "Condition", "Refund outcome"),
            [
                ("A", "Unopened or like new, complete", "Full refund."),
                (
                    "B",
                    "Opened, complete and working",
                    "Full refund, less restocking fee if section 2.4 applies.",
                ),
                ("C", "Missing parts or cosmetic damage", "Refund less 20% of the item price."),
                (
                    "D",
                    "Physical or liquid damage, or not working without a defect report",
                    "Refund denied; Team Lead review. The unit is shipped back to the customer "
                    "at no cost.",
                ),
            ],
            widths=(0.6, 2.0, 2.6),
            caption="Table 4-2. Grade-based refund outcomes.",
        ),
        h2("4.5 Returnless Refunds"),
        p(
            "If the item price is $40.00 or less and the customer reports a defect that "
            "troubleshooting confirms, the agent may issue a refund or free replacement "
            "without requiring the item to be returned. Returnless refunds are limited to "
            "one per customer per 12 months and do not require Team Lead approval. The "
            "Room Sensor S1 single pack is the most common case."
        ),
        h1("5. Exceptions"),
        bullets(
            "**Late returns:** a Team Lead may approve a return up to 15 days after the "
            "window has closed, once per customer. Note the reason in the ticket.",
            "**Chargebacks:** if the customer has opened a card dispute, do not process a "
            "refund. Route the ticket to the Finance Disputes queue.",
            "**Repeat returners:** customers with three or more returns in 12 months are "
            "flagged in OMS. Refunds for flagged customers need Team Lead approval "
            "regardless of amount.",
            "**Price adjustments** within 14 days of purchase follow the price match "
            "rules in the Billing FAQ and are not processed as returns.",
        ),
        h1("6. Quality and Records"),
        p(
            "Every return must have an RMA number linked to a LumoraDesk ticket. Quality "
            "Assurance audits 5% of refunds each month. Audit findings are reviewed with "
            "the agent's Team Lead within 10 business days."
        ),
        table(
            ("Revision", "Date", "Change"),
            [
                ("2.3", "January 5, 2026", "Holiday extension excludes business accounts."),
                ("2.2", "July 1, 2025", "Returnless refund limit raised to $40."),
                ("2.1", "February 3, 2025", "Grade-based refund table added."),
            ],
            widths=(0.8, 1.3, 3.0),
        ),
    ),
    facts=(
        fact(
            "SOP-RET-01",
            "Products bought directly from Lumora can be returned within 30 calendar days "
            "of the delivery date (not the order date).",
            "within 30 calendar days of the delivery date",
        ),
        fact(
            "SOP-RET-02",
            "Holiday extension: orders delivered between November 15 and December 31 can "
            "be returned until January 31, but not for business accounts or orders with "
            "more than five units of the same product.",
            "Orders delivered between November 15 and December 31",
            "more than five units of the same product",
            kind="cross-page",
        ),
        fact(
            "SOP-RET-03",
            "A 15% restocking fee applies to opened change-of-mind returns when the RMA is "
            "created more than 14 days after delivery.",
            "A 15% restocking fee applies to opened change-of-mind returns",
        ),
        fact(
            "SOP-RET-04",
            "Refunds from $250.01 to $1,000.00 per order must be approved by a Team Lead.",
            "$250.01 to $1,000.00",
            kind="table",
        ),
        fact(
            "SOP-RET-05",
            "Refunds above $5,000.00 require both the Customer Care Manager and the Finance "
            "Controller.",
            "Customer Care Manager and Finance Controller",
            kind="table",
        ),
        fact(
            "SOP-RET-06",
            "Refunds are issued within 5 business days after the RPC records a passed "
            "inspection; card refunds can take another 3 to 10 business days to appear.",
            "within 5 business days after the RPC records a passed inspection",
        ),
        fact(
            "SOP-RET-07",
            "The $129 professional installation fee is refunded in full only if the "
            "appointment has not yet taken place.",
            "installation fee is refunded in full only if the appointment",
        ),
        fact(
            "SOP-RET-08",
            "A Grade C return (missing parts or cosmetic damage) is refunded less 20% of "
            "the item price.",
            "Refund less 20% of the item price.",
            kind="table",
        ),
        fact(
            "SOP-RET-09",
            "Returnless refunds are allowed for items priced $40.00 or less with a "
            "confirmed defect, limited to one per customer per 12 months.",
            "If the item price is $40.00 or less",
        ),
        fact(
            "SOP-RET-10",
            "Damaged-in-transit returns (reason code DT-04) must be reported within 7 days "
            "of delivery.",
            "Damaged in transit (report within 7 days of delivery)",
            kind="table",
        ),
    ),
)

# ---------------------------------------------------------------- warranty

WARRANTY_CLAIMS = SampleDoc(
    filename="SOP - Warranty Claims.pdf",
    title="Warranty Claims SOP",
    doc_type="sop",
    doc_number="LHS-SOP-TS-007",
    revision="4.0",
    effective_date="February 16, 2026",
    owner="Technical Support (Tier 2)",
    audience="Technical Support agents, Warranty Supervisors, Customer Care Team Leads",
    purpose=(
        "Defines how warranty claims are verified, approved and fulfilled for Lumora "
        "devices after the 30-day return window. Coverage terms themselves are defined "
        "in the Lumora Limited Warranty Policy (LHS-POL-001); if this SOP and the policy "
        "disagree, the policy prevails."
    ),
    blocks=(
        h1("1. Scope"),
        p(
            "This SOP applies to claims for hardware defects reported more than 30 days "
            "after delivery and within the warranty period. Problems reported within 30 "
            "days of delivery are handled as defective returns under the Returns and "
            "Refunds SOP (LHS-SOP-CC-004), unless the customer prefers a replacement. "
            "Units reported dead on arrival within 14 days of delivery are handled as DOA "
            "RMAs (see LHS-SOP-OPS-011)."
        ),
        h1("2. Warranty Periods Quick Reference"),
        table(
            ("Product", "Standard term", "Notes"),
            [
                ("Thermostat T2", "24 months", "No extension for professional installation."),
                (
                    "Thermostat T3",
                    "36 months",
                    "Can be extended to 48 months; see policy section 5.",
                ),
                ("Room Sensor S1", "12 months", "Battery not covered."),
                ("Hub H1", "24 months", ""),
                ("Power Extender Kit PEK-1", "12 months", ""),
                ("Certified Refurbished units", "12 months (S1: 6 months)", "Regardless of model."),
            ],
            widths=(1.6, 1.4, 2.4),
            caption="Table 2-1. Warranty terms (summary of LHS-POL-001).",
        ),
        h1("3. Claim Intake"),
        steps(
            "Verify the customer's identity and open or link a LumoraDesk ticket.",
            "Record the serial number from the app (Device > About) or from the label on "
            "the back of the device. Serial numbers start with the model prefix, for "
            "example T3B for Thermostat T3 hardware revision B.",
            "Confirm that the device is within the warranty period. The warranty start date "
            "is the delivery date registered for the serial number.",
            "If the serial number is not registered to the customer's account, request "
            "proof of purchase: an order number or a receipt showing the purchase date and "
            "an authorized retailer.",
            "Confirm and record the troubleshooting performed. At minimum: a power-cycle, a "
            "firmware version check, and the model-specific steps in the product guide.",
            "For any report of physical damage, request at least two photos of the device "
            "and its wiring.",
            "Check the claim against the exclusions in policy section 4. If an exclusion "
            "applies, follow section 6 (denied claims).",
        ),
        note(
            "Do not ask the customer to open the device or remove the T3 battery. Opening "
            "the device is not required for any claim and may create a safety risk.",
            label="Important",
        ),
        h1("4. Approval Rules"),
        p(
            "Tier 2 agents may approve warranty claims that meet all intake requirements. "
            "Each customer account may have up to two approved warranty claims in any "
            "rolling 12-month period. A third claim within 12 months must be reviewed by a "
            "Warranty Supervisor before approval, because repeated claims can indicate an "
            "installation problem or abuse of the program."
        ),
        p(
            "The claim decision must be communicated to the customer within 2 business "
            "days of receiving complete documentation. Use the email templates WC-APPROVED "
            "or WC-DENIED in LumoraDesk. Claims for devices bought from unauthorized "
            "resellers (including online marketplace sellers not listed on the Lumora "
            "website) are denied."
        ),
        page_break(),
        h1("5. Fulfilment Options"),
        h2("5.1 Standard Replacement"),
        p(
            "The customer ships the defective unit to the RPC using an RMA of type WAR. A "
            "replacement ships within 2 business days after the RPC confirms receipt. The "
            "replacement may be new or Certified Refurbished and is covered for the "
            "remainder of the original warranty or 90 days, whichever is longer."
        ),
        h2("5.2 Advance Replacement"),
        p(
            "With advance replacement, the replacement ships before the defective unit is "
            "returned. Advance replacement is offered to all customers for the Thermostat "
            "T3 and the Hub H1, and for any device when the customer has an active Lumora "
            "Plus subscription. It is not offered for the T2 or S1 to customers without "
            "Lumora Plus. To start an advance replacement, create an RMA of type ADV and "
            "place a card authorization hold equal to the current list price of the "
            "device. The hold is released when the RPC receives the defective unit. "
            "If the defective unit is not received within 21 days of the replacement "
            "delivery, the customer's card is charged the full list price and the RMA is "
            "closed as unreturned."
        ),
        h2("5.3 Refund Instead of Replacement"),
        p(
            "If a replacement cannot be shipped within 10 business days because of stock "
            "shortages, the agent may offer a refund of the original purchase price as an "
            "alternative. Refunds in lieu of replacement up to $250 may be approved by "
            "Tier 2; higher amounts follow the refund approval matrix in LHS-SOP-CC-004."
        ),
        table(
            ("Option", "Who qualifies", "Customer pays shipping", "Typical time to replacement"),
            [
                ("Standard replacement", "All valid claims", "No", "5-7 business days"),
                (
                    "Advance replacement",
                    "T3 and H1 (all customers); any device with Lumora Plus",
                    "No",
                    "2-3 business days",
                ),
                (
                    "Refund in lieu",
                    "Replacement out of stock for more than 10 business days",
                    "No",
                    "Not applicable",
                ),
            ],
            widths=(1.3, 2.2, 1.0, 1.2),
            caption="Table 5-1. Fulfilment options.",
        ),
        h1("6. Denied Claims and Appeals"),
        p(
            "When a claim is denied, the agent must state the specific exclusion from the "
            "policy in the WC-DENIED email. Customers may appeal within 30 days of the "
            "decision by replying to the email. A Warranty Supervisor reviews the appeal "
            "and responds within 5 business days. A second appeal is not available."
        ),
        h1("7. Out-of-Warranty Requests"),
        p(
            "If the device is no more than 90 days past the end of its warranty, the agent "
            "may offer a one-time loyalty discount of 30% on a new replacement unit using "
            "discount code type LOYAL-30. Devices more than 90 days out of warranty are "
            "not eligible for the discount; the customer may buy a replacement at the "
            "normal price."
        ),
        h1("8. Common Claim Scenarios"),
        p(
            "The table below gives the expected decision for situations that agents ask "
            "about most often. When a case does not match any scenario, ask a Warranty "
            "Supervisor before deciding."
        ),
        table(
            ("Scenario", "Decision", "Reason / next step"),
            [
                (
                    "T3 shows E4 after a power-cycle, 20 months after delivery",
                    "Approve",
                    "Humidity sensor fault, within the 36-month term.",
                ),
                (
                    "T2 display failed 26 months after delivery",
                    "Deny",
                    "Outside the 24-month T2 term; offer LOYAL-30 if within 90 days.",
                ),
                (
                    "T3 battery holds only a few minutes, 14 months after delivery",
                    "Deny",
                    "T3 battery coverage is 12 months (policy section 1).",
                ),
                (
                    "Terminals melted after the customer wired the T2 to a baseboard heater",
                    "Deny",
                    "Line-voltage exclusion; treat as a safety case first.",
                ),
                (
                    "S1 bought from a marketplace seller not listed as authorized",
                    "Deny",
                    "Unauthorized reseller exclusion.",
                ),
                (
                    "H1 solid red light returns after a power-cycle",
                    "Approve",
                    "Confirmed hardware fault; advance replacement available.",
                ),
                (
                    "Third claim on the same account in 10 months",
                    "Hold",
                    "Warranty Supervisor review required (section 4).",
                ),
            ],
            widths=(2.3, 0.7, 2.2),
            caption="Table 8-1. Claim scenarios and expected decisions.",
        ),
        h2("8.1 Claim Checklist"),
        bullets(
            "Serial number recorded and matches the account or proof of purchase",
            "Warranty start date and end date confirmed",
            "Troubleshooting documented, including the firmware version",
            "Photos attached for any physical damage",
            "Exclusions checked and decision recorded with the template name",
            "RMA created with the correct type (WAR or ADV) and linked to the ticket",
        ),
        h1("9. Records"),
        bullets(
            "Every claim, approved or denied, must be logged with the serial number, "
            "warranty start date, troubleshooting performed and decision.",
            "Photos and proof of purchase are attached to the LumoraDesk ticket, not sent "
            "by personal email.",
            "Warranty Supervisors review a weekly report of accounts with two or more "
            "claims in 12 months.",
        ),
        h1("10. Fraud Indicators"),
        p(
            "Most claims are genuine. The indicators below do not justify a denial on their "
            "own, but any claim with two or more of them must be reviewed by a Warranty "
            "Supervisor before approval:"
        ),
        bullets(
            "The serial number was registered to a different account in the last 90 days.",
            "The shipping address for the replacement differs from the address where the "
            "device is registered.",
            "The customer asks for advance replacement and refuses a card authorization hold.",
            "Photos show a device of a different model or hardware revision than the serial "
            "number.",
            "The account has a chargeback or a flagged return in the last 12 months.",
        ),
        h1("11. Communicating Decisions"),
        p(
            "Decision emails are sent from LumoraDesk using the approved templates. Agents "
            "may add a personal sentence but must not change the policy wording. The "
            "WC-APPROVED template includes the RMA number, the fulfilment option and the "
            "shipping deadline for the defective unit. The WC-DENIED template includes the "
            "exclusion that applies, the appeal process in section 6 and, where eligible, "
            "the LOYAL-30 offer in section 7."
        ),
        p(
            "If the customer disagrees on a call, explain the reason calmly, offer the "
            "appeal process, and do not promise a different outcome. Agents may not "
            "approve a denied claim as a goodwill gesture; goodwill credits follow the "
            "Ticket Escalation SOP."
        ),
    ),
    facts=(
        fact(
            "SOP-WAR-01",
            "Each customer account may have up to two approved warranty claims in a rolling "
            "12-month period; a third claim requires Warranty Supervisor review.",
            "up to two approved warranty claims in any rolling 12-month period",
        ),
        fact(
            "SOP-WAR-02",
            "Warranty claim decisions must be communicated within 2 business days of "
            "receiving complete documentation.",
            "within 2 business days of receiving complete documentation",
        ),
        fact(
            "SOP-WAR-03",
            "Advance replacement is offered to all customers for the T3 and H1, and for any "
            "device with an active Lumora Plus subscription, with a card hold equal to the "
            "list price; if the defective unit is not received within 21 days the card is "
            "charged.",
            "Advance replacement is offered to all customers for the Thermostat",
            kind="text",
            tags=("confusable",),
        ),
        fact(
            "SOP-WAR-04",
            "For advance replacements, the customer is charged the full list price if the "
            "defective unit is not received within 21 days of the replacement delivery.",
            "not received within 21 days of the replacement delivery",
        ),
        fact(
            "SOP-WAR-05",
            "If a replacement cannot ship within 10 business days due to stock shortages, "
            "the agent may offer a refund of the original purchase price.",
            "cannot be shipped within 10 business days",
        ),
        fact(
            "SOP-WAR-06",
            "Customers may appeal a denied warranty claim within 30 days; a Warranty "
            "Supervisor responds within 5 business days, and no second appeal is allowed.",
            "appeal within 30 days of the decision",
        ),
        fact(
            "SOP-WAR-07",
            "Devices no more than 90 days past warranty may get a one-time 30% loyalty "
            "discount on a new replacement (code type LOYAL-30).",
            "one-time loyalty discount of 30%",
        ),
        fact(
            "SOP-WAR-08",
            "Certified Refurbished units have a 12-month warranty, except the S1 which has "
            "6 months.",
            "12 months (S1: 6 months)",
            kind="table",
        ),
    ),
)

# -------------------------------------------------------------- escalation

TICKET_ESCALATION = SampleDoc(
    filename="SOP - Ticket Escalation.pdf",
    title="Ticket Escalation SOP",
    doc_type="sop",
    doc_number="LHS-SOP-CC-002",
    revision="5.2",
    effective_date="March 30, 2026",
    owner="Customer Care Operations",
    audience="All support tiers, Team Leads, Escalations Desk, on-call engineering",
    purpose=(
        "Defines ticket priorities, service level targets and the rules for escalating "
        "tickets between support tiers, to management and to the Safety Officer."
    ),
    blocks=(
        h1("1. Support Tiers"),
        table(
            ("Tier / team", "Responsibility"),
            [
                (
                    "Tier 1 - Customer Care",
                    "First contact for all channels: orders, "
                    "returns, billing, basic setup and troubleshooting.",
                ),
                (
                    "Tier 2 - Technical Support",
                    "Advanced troubleshooting, wiring "
                    "questions, warranty claims, installer support.",
                ),
                (
                    "Tier 3 - Product Engineering",
                    "Firmware and hardware defects, incident "
                    "investigation. Accepts escalations only from Tier 2.",
                ),
                (
                    "Escalations Desk",
                    "Complaints involving executives, media, social media or regulators.",
                ),
                (
                    "Safety Officer",
                    "Owner of all safety cases (fire, smoke, burns, "
                    "electrical shock, swollen batteries).",
                ),
            ],
            widths=(1.6, 3.6),
        ),
        h1("2. Priority Levels and SLAs"),
        p(
            "Every ticket is assigned a priority when it is created. The priority can be "
            "raised at any time but may only be lowered by a Team Lead. SLA clocks for P1 "
            "run 24 hours a day; all other priorities use business hours (Monday to "
            "Friday, 8:00 AM to 8:00 PM Eastern)."
        ),
        table(
            ("Priority", "Definition", "First response", "Customer updates", "Resolution target"),
            [
                (
                    "P1 - Critical",
                    "Safety hazard, or no heat when indoor temperature is below 50 °F",
                    "15 minutes",
                    "Every 2 hours",
                    "4 hours",
                ),
                (
                    "P2 - High",
                    "System cannot be controlled at all, or an issue affects multiple customers",
                    "1 hour",
                    "Every business day",
                    "1 business day",
                ),
                (
                    "P3 - Normal",
                    "Single device fault with a workaround",
                    "4 business hours",
                    "Every 2 business days",
                    "3 business days",
                ),
                (
                    "P4 - Low",
                    "How-to questions, feature requests, cosmetic issues",
                    "1 business day",
                    "On resolution",
                    "10 business days",
                ),
            ],
            widths=(0.9, 2.2, 0.9, 1.0, 1.0),
            caption="Table 2-1. Priority matrix.",
        ),
        note(
            "An SLA alert is sent automatically when 80% of the first response or "
            "resolution time has elapsed. Team Leads must reassign or escalate the ticket "
            "before the SLA is breached.",
        ),
        h1("3. Escalating Between Tiers"),
        h2("3.1 Tier 1 to Tier 2"),
        p("Tier 1 agents must escalate to Tier 2 when any of the following applies:"),
        bullets(
            "The issue is not resolved after 20 minutes of active troubleshooting on a "
            "call or chat.",
            "The customer contacts Lumora for the second time about the same issue within 7 days.",
            "The product guide lists the error code as an escalation trigger.",
            "The caller is a Lumora Certified Installer.",
            "The issue involves wiring changes at the HVAC equipment.",
        ),
        h2("3.1.1 How to Escalate in LumoraDesk"),
        steps(
            "Complete the handoff summary fields described in section 7.1.",
            "Change the ticket group to Tier 2 - Technical Support and keep the current "
            "priority unless the escalation criteria require a higher one.",
            "Tell the customer that a specialist will contact them and give the response "
            "time for the ticket priority from Table 2-1.",
            "Do not close or set the ticket to Pending after escalating; the receiving tier "
            "owns the next action.",
        ),
        h2("3.2 Tier 2 to Tier 3"),
        p(
            "Tier 2 escalates to Tier 3 Product Engineering when a firmware defect can be "
            "reproduced, or when a hardware failure pattern appears in units from the same "
            "production lot (the lot code is the 4-digit number after the model prefix in "
            "the serial number). The escalation must include the serial numbers, firmware "
            "versions, steps to reproduce and logs exported from the app. Tier 3 "
            "acknowledges escalations within 1 business day and may return a ticket to "
            "Tier 2 if required information is missing. Tier 2 keeps ownership of all "
            "customer communication while Tier 3 investigates."
        ),
        p(
            "**Incident rule.** When three or more customers report the same issue within "
            "24 hours, Tier 2 must open an Incident ticket (INC) and page the on-call "
            "engineer, even if the issue cannot yet be reproduced. All matching customer "
            "tickets are linked to the INC ticket as children and set to P2. The incident "
            "owner posts a status update for agents every 4 hours until the incident is "
            "resolved, and Customer Care Operations decides within 2 hours whether a "
            "banner message is shown in the app."
        ),
        h1("4. Safety Escalations"),
        p(
            "Any report of smoke, fire, a burning smell, scorch marks, melted terminals, "
            "electrical shock or a swollen battery is a safety case. Safety cases are "
            "always P1, regardless of the product or the customer's request."
        ),
        steps(
            "Instruct the customer to switch off power to the HVAC system at the circuit "
            "breaker. If there is smoke or fire, tell the customer to leave the building "
            "and call emergency services, and end troubleshooting.",
            "Create or update the ticket as P1 with the category Safety.",
            "Notify the Safety Officer through the safety hotline queue within 1 hour of "
            "the first report, at any time of day.",
            "Ask the customer to keep the device and not to discard it. Do not request "
            "photos while there is any ongoing hazard.",
            "The Safety Officer informs Tier 3 Product Engineering and Legal within 24 "
            "hours and owns all further customer communication.",
        ),
        note(
            "Agents must never suggest that a safety case was caused by the customer, and "
            "must not offer compensation. Compensation for safety cases is decided only by "
            "the Safety Officer.",
            label="Important",
        ),
        h1("5. Management Escalations"),
        bullets(
            "**Customer asks for a supervisor:** create a callback task for a Team Lead. "
            "The Team Lead must call back within 4 business hours.",
            "**Social media, press or regulator mentions:** route to the Escalations Desk "
            "the same business day. Agents do not respond publicly.",
            "**Executive complaints** (emails addressed to company officers): handled only "
            "by the Escalations Desk, first response within 1 business day.",
        ),
        page_break(),
        h1("6. Goodwill Credits"),
        p(
            "Goodwill credits compensate customers for poor experiences, such as missed "
            "callbacks or repeated contacts. They are issued as store credit and do not "
            "replace refunds owed under the Returns and Refunds SOP."
        ),
        table(
            ("Role", "Maximum credit per ticket"),
            [
                ("Tier 1 agent", "$25"),
                ("Tier 2 agent", "$75"),
                ("Team Lead", "$200"),
                ("Customer Care Manager", "Above $200"),
            ],
            widths=(2.0, 2.0),
            caption="Table 6-1. Goodwill credit limits.",
        ),
        p(
            "A customer can receive at most one goodwill credit per 90 days without "
            "Customer Care Manager approval. Credits are not given for safety cases (see "
            "section 4)."
        ),
        h1("7. Handoff and Closure Requirements"),
        h2("7.1 Handoff Summary"),
        p("Every escalation must include a summary with these fields:"),
        bullets(
            "Customer name, account email and device serial numbers",
            "Problem statement in one sentence and when it started",
            "Troubleshooting already done, with results",
            "Customer expectation and any commitments made",
            "Priority and SLA deadline",
        ),
        h2("7.2 Warm Transfers"),
        p(
            "P1 and P2 escalations by phone must be warm transfers: the agent stays on the "
            "line and introduces the case to the receiving agent. If no agent is available "
            "within 5 minutes, the ticket is escalated in LumoraDesk and the customer is "
            "told when to expect a callback."
        ),
        h2("7.3 Closing Escalated Tickets"),
        p(
            "Escalated tickets may only be closed after the customer confirms the issue is "
            "resolved, or after three contact attempts over 5 business days without a "
            "reply. The closing note must state which of these applied."
        ),
        h1("8. Priority Examples"),
        p(
            "Use these examples to set the priority consistently. When a ticket matches "
            "more than one example, use the highest priority."
        ),
        table(
            ("Situation", "Priority", "Route to"),
            [
                (
                    "Customer smells burning plastic near the thermostat",
                    "P1",
                    "Safety Officer and Tier 2",
                ),
                ("No heat, indoor temperature 47 °F, outdoor temperature 20 °F", "P1", "Tier 2"),
                ("No heat, indoor temperature 62 °F", "P2", "Tier 2"),
                ("Thermostat offline in the app but heating works", "P3", "Tier 1"),
                ("Room sensor battery drains in 3 months", "P3", "Tier 1"),
                (
                    "Twelve customers report E12 after the same firmware update",
                    "P2 (INC)",
                    "Tier 2, then Tier 3",
                ),
                ("Customer asks how to set a vacation schedule", "P4", "Tier 1"),
                ("Customer threatens to post a complaint video online", "P3", "Escalations Desk"),
            ],
            widths=(2.8, 0.8, 1.6),
            caption="Table 8-1. Priority examples.",
        ),
        h1("9. Reporting"),
        p(
            "Customer Care Operations publishes a weekly SLA report showing breaches by "
            "priority and team. Two or more P1 breaches in a calendar month trigger a "
            "review with the Director of Customer Experience."
        ),
    ),
    facts=(
        fact(
            "SOP-ESC-01",
            "P1 (Critical) tickets require a first response within 15 minutes and have a "
            "4-hour resolution target; P1 covers safety hazards or no heat when indoor "
            "temperature is below 50 °F.",
            "below 50 °F",
            kind="table",
        ),
        fact(
            "SOP-ESC-02",
            "P3 (Normal) tickets have a first response target of 4 business hours and a "
            "resolution target of 3 business days.",
            "Every 2 business days",
            kind="table",
        ),
        fact(
            "SOP-ESC-03",
            "Tier 1 must escalate to Tier 2 after 20 minutes of active troubleshooting "
            "without resolution, or on a second contact about the same issue within 7 days.",
            "not resolved after 20 minutes of active troubleshooting",
        ),
        fact(
            "SOP-ESC-04",
            "When three or more customers report the same issue within 24 hours, Tier 2 "
            "must open an Incident (INC) ticket and page the on-call engineer; linked "
            "tickets are set to P2 and updates are posted every 4 hours.",
            "When three or more customers report the same issue within",
            "posts a status update for agents every 4 hours",
            kind="cross-page",
        ),
        fact(
            "SOP-ESC-05",
            "In a safety case the Safety Officer must be notified within 1 hour of the "
            "first report, at any time of day.",
            "within 1 hour of the first report",
        ),
        fact(
            "SOP-ESC-06",
            "Goodwill credit limits per ticket: Tier 1 $25, Tier 2 $75, Team Lead $200; "
            "above $200 needs the Customer Care Manager.",
            "Maximum credit per ticket",
            kind="table",
        ),
        fact(
            "SOP-ESC-07",
            "When a customer asks for a supervisor, a Team Lead must call back within 4 "
            "business hours.",
            "The Team Lead must call back within 4 business hours.",
        ),
        fact(
            "SOP-ESC-08",
            "Escalated tickets may be closed only after customer confirmation or three "
            "contact attempts over 5 business days.",
            "three contact attempts over 5 business days",
        ),
        fact(
            "SOP-ESC-09",
            "A customer can receive at most one goodwill credit per 90 days without "
            "Customer Care Manager approval.",
            "at most one goodwill credit per 90 days",
        ),
    ),
)

# --------------------------------------------------------------------- RMA

RMA_PROCESS = SampleDoc(
    filename="SOP - RMA Process.pdf",
    title="RMA Process SOP",
    doc_type="sop",
    doc_number="LHS-SOP-OPS-011",
    revision="3.0",
    effective_date="November 3, 2025",
    owner="Returns Operations",
    audience="Customer Care, Technical Support, Returns Processing Center staff",
    purpose=(
        "Defines how Return Merchandise Authorizations (RMAs) are created, how returned "
        "units are received, inspected and graded at the Returns Processing Center (RPC), "
        "and how RMAs are closed."
    ),
    blocks=(
        h1("1. RMA Types"),
        table(
            ("Type", "Used for", "Created by", "Outcome after inspection"),
            [
                (
                    "RET",
                    "Returns for refund within the return window",
                    "Tier 1",
                    "Refund per LHS-SOP-CC-004",
                ),
                ("WAR", "Warranty claims - standard replacement", "Tier 2", "Replacement ships"),
                ("ADV", "Warranty claims - advance replacement", "Tier 2", "Card hold released"),
                (
                    "DOA",
                    "Device dead on arrival, reported within 14 days of delivery",
                    "Tier 1 or Tier 2",
                    "Replacement ships by expedited shipping at no cost",
                ),
            ],
            widths=(0.6, 2.2, 1.0, 1.8),
            caption="Table 1-1. RMA types.",
        ),
        h1("2. RMA Numbers and Validity"),
        p(
            "RMA numbers use the format RMA-YYMM-NNNNN, where YYMM is the year and month "
            "of creation and NNNNN is a sequence number, for example RMA-2603-00417. An "
            "RMA is valid for 30 days from creation. The customer must ship the item "
            "within 14 days; RMAs with no carrier scan after 14 days receive an automatic "
            "reminder email, and RMAs still open after 30 days are cancelled "
            "automatically."
        ),
        p(
            "Only one RMA may be open per serial number. If a customer needs to change the "
            "RMA type (for example from RET to WAR), cancel the open RMA and create a new "
            "one rather than editing the type."
        ),
        h1("3. Creating an RMA"),
        steps(
            "Open the order or the device record in OMS and select Create RMA.",
            "Choose the RMA type from Table 1-1 and the reason code from the Returns and "
            "Refunds SOP or the warranty claim.",
            "Enter the serial number of every unit being returned. OMS rejects serial "
            "numbers that do not belong to the order or account.",
            "Select the return method: prepaid label (default), carrier pickup (bulk "
            "RMAs only) or battery return kit (see section 7).",
            "Add the LumoraDesk ticket number and save. OMS emails the RMA number and "
            "packing instructions to the customer.",
        ),
        h2("3.1 Bulk RMAs"),
        p(
            "RMAs for 10 or more units on one account, typically from installers or "
            "property managers, require approval from the Operations Manager before the "
            "RMA is released. Bulk RMAs ship by freight pickup on a pallet, scheduled by "
            "the RPC within 3 business days of approval."
        ),
        h1("4. Receiving at the RPC"),
        steps(
            "Scan the RMA number on the package label. Packages must be logged in OMS "
            "within 1 business day of arrival at the RPC.",
            "Open the package and compare the serial number on each unit with the serial "
            "numbers on the RMA.",
            "Inspect and grade each unit within 3 business days of arrival (section 5).",
            "Record the grade and disposition in OMS. This triggers the outcome in Table "
            "1-1 automatically within 1 business day.",
        ),
        h2("4.1 Exceptions at Receiving"),
        table(
            ("Exception", "Handling"),
            [
                (
                    "Serial number does not match the RMA",
                    "Place the unit on hold and ask "
                    "Customer Care to contact the customer. If the discrepancy is not "
                    "resolved within 5 business days, process the RMA as not received and "
                    "return the unit to the customer.",
                ),
                (
                    "Package arrives without an RMA number",
                    "Move to the quarantine shelf "
                    "for 10 business days while Customer Care tries to identify the sender. "
                    "Unidentified units are then scrapped and recorded as unclaimed.",
                ),
                (
                    "Wrong product received",
                    "Hold the item and contact the customer; the "
                    "RMA stays open until the correct item arrives or the RMA expires.",
                ),
                (
                    "Visible battery swelling or leak",
                    "Stop handling. Move the package to "
                    "the hazardous materials cabinet and notify the RPC supervisor "
                    "immediately.",
                ),
            ],
            widths=(1.6, 3.6),
            caption="Table 4-1. Receiving exceptions.",
        ),
        h1("5. Inspection and Grading"),
        p(
            "Inspectors power on every unit on the test bench, confirm it connects to the "
            "test network, run the automated self-test and check for physical damage, "
            "liquid indicators and missing parts. Each unit receives one grade:"
        ),
        table(
            ("Grade", "Criteria", "Disposition"),
            [
                (
                    "A",
                    "Unopened, or opened with all parts and no signs of use",
                    "RTS - return to stock as new",
                ),
                (
                    "B",
                    "Opened, complete, passes self-test, minor signs of use",
                    "RFB - refurbish and sell as Certified Refurbished",
                ),
                (
                    "C",
                    "Missing parts or cosmetic damage, passes self-test",
                    "RFB, or harvest for parts if refurbishing is not economical",
                ),
                (
                    "D",
                    "Fails self-test, physical or liquid damage",
                    "SCR - scrap and "
                    "recycle; RTV - return to vendor if defect rate tracking applies",
                ),
            ],
            widths=(0.6, 2.6, 2.2),
            caption="Table 5-1. Inspection grades and dispositions.",
        ),
        p(
            "Units returned under a WAR or ADV RMA that fail the self-test are recorded as "
            "confirmed defects. Units that pass the self-test with no fault found are "
            "graded normally, and the result is added to the warranty claim record."
        ),
        h1("6. Closing an RMA"),
        bullets(
            "RET: the refund is released in OMS within 1 business day of the inspection "
            "result; Customer Care confirms the amount to the customer.",
            "WAR: the replacement is picked, packed and shipped within 2 business days of receipt.",
            "ADV: the card authorization hold is released; if the unit is not received "
            "within 21 days of the replacement delivery the card is charged.",
            "DOA: the replacement ships by expedited shipping the same business day when "
            "the RMA is created before 12:00 PM Eastern, without waiting for the return.",
        ),
        h1("7. Returning Devices With Batteries"),
        p(
            "The Thermostat T3 contains a lithium-ion battery. A T3 that is reported with a "
            "swollen, hot or leaking battery must not be shipped with a standard prepaid "
            "label. Instead, select the return method Battery Return Kit when creating the "
            "RMA. The RPC sends kit BRK-1, a fire-resistant pouch with a "
            "hazardous-materials label, by ground shipping within 2 business days, and the "
            "customer must not return the device until the kit arrives. Undamaged T3 units "
            "and all other products ship normally."
        ),
        h1("8. Performance Targets"),
        table(
            ("Metric", "Target"),
            [
                ("Dock to logged in OMS", "1 business day"),
                ("Dock to inspected and graded", "3 business days"),
                ("Dock to stock (Grade A)", "5 business days"),
                ("RMAs open longer than 30 days", "0 (auto-cancelled)"),
            ],
            widths=(2.4, 2.0),
            caption="Table 8-1. RPC performance targets.",
        ),
        p(
            "The RPC supervisor reviews the targets weekly with Returns Operations. "
            "Grade D rates above 8% for any product in a calendar month are reported to "
            "Product Engineering as a possible quality issue."
        ),
        h1("9. Roles and Responsibilities"),
        table(
            ("Role", "Responsibilities"),
            [
                (
                    "Customer Care (Tier 1)",
                    "Creates RET and DOA RMAs, sends labels, answers "
                    "customer questions about RMA status.",
                ),
                (
                    "Technical Support (Tier 2)",
                    "Creates WAR and ADV RMAs after an approved "
                    "warranty claim; manages card holds for ADV.",
                ),
                (
                    "RPC receiving clerk",
                    "Logs packages, verifies serial numbers, handles receiving exceptions.",
                ),
                ("RPC inspector", "Runs the test bench, grades units and records dispositions."),
                (
                    "RPC supervisor",
                    "Hazardous materials handling, weekly target review, "
                    "approval of scrap batches.",
                ),
                ("Operations Manager", "Approves bulk RMAs and exceptions to this SOP."),
            ],
            widths=(1.6, 3.6),
            caption="Table 9-1. RMA roles.",
        ),
        h2("9.1 Answering RMA Status Questions"),
        p(
            "Agents can see the RMA status in OMS: Created, Label Sent, In Transit, "
            "Received, Inspected, Closed or Cancelled. If a customer asks why a refund or "
            "replacement has not arrived, check the status first. Received but not "
            "inspected after 3 business days is a breach of the RPC target and should be "
            "reported to the RPC supervisor queue rather than promised to the customer as "
            "a date."
        ),
    ),
    facts=(
        fact(
            "SOP-RMA-01",
            "RMA numbers use the format RMA-YYMM-NNNNN; an RMA is valid for 30 days and the "
            "customer must ship within 14 days.",
            "RMA-YYMM-NNNNN",
        ),
        fact(
            "SOP-RMA-02",
            "A DOA RMA is for a device reported dead on arrival within 14 days of delivery; "
            "the replacement ships by expedited shipping at no cost.",
            "Device dead on arrival, reported within 14 days of delivery",
            kind="table",
        ),
        fact(
            "SOP-RMA-03",
            "RMAs for 10 or more units on one account require Operations Manager approval.",
            "RMAs for 10 or more units on one account",
        ),
        fact(
            "SOP-RMA-04",
            "Returned packages must be logged in OMS within 1 business day of arrival and "
            "inspected within 3 business days.",
            "within 1 business day of arrival at the RPC",
        ),
        fact(
            "SOP-RMA-05",
            "Packages without an RMA number are quarantined for 10 business days, then "
            "unidentified units are scrapped.",
            "quarantine shelf for 10 business days",
            kind="table",
        ),
        fact(
            "SOP-RMA-06",
            "A serial-number mismatch is held for up to 5 business days; if unresolved, the "
            "RMA is processed as not received and the unit returned to the customer.",
            "resolved within 5 business days, process the RMA as not received",
            kind="table",
        ),
        fact(
            "SOP-RMA-07",
            "A T3 with a swollen, hot or leaking battery must be returned with Battery "
            "Return Kit BRK-1, not a standard prepaid label.",
            "The RPC sends kit BRK-1",
        ),
        fact(
            "SOP-RMA-08",
            "Grade B returns (opened, complete, passes self-test) are refurbished and sold "
            "as Certified Refurbished (disposition RFB).",
            "refurbish and sell as Certified Refurbished",
            kind="table",
        ),
        fact(
            "SOP-RMA-09",
            "Grade D rates above 8% for any product in a month are reported to Product "
            "Engineering.",
            "Grade D rates above 8%",
        ),
    ),
)

SOPS = (RETURNS_AND_REFUNDS, WARRANTY_CLAIMS, TICKET_ESCALATION, RMA_PROCESS)
