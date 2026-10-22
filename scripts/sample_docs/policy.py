"""Lumora Limited Warranty Policy."""

from scripts.sample_docs.model import (
    SampleDoc,
    bullets,
    fact,
    h1,
    h2,
    note,
    p,
    page_break,
    table,
)

WARRANTY_POLICY = SampleDoc(
    filename="Policy - Limited Warranty.pdf",
    title="Lumora Limited Warranty Policy",
    doc_type="policy",
    doc_number="LHS-POL-001",
    revision="2026.1",
    effective_date="January 1, 2026",
    owner="Legal and Compliance",
    audience="All employees; customer-facing summary published on the Lumora website",
    purpose=(
        "States the terms of the limited hardware warranty for Lumora devices sold in "
        "the United States on or after the effective date. This policy is the source of "
        "truth for coverage; operational steps are described in the Warranty Claims SOP "
        "(LHS-SOP-TS-007)."
    ),
    blocks=(
        h1("1. Coverage Terms"),
        h2("1.1 Definitions"),
        table(
            ("Term", "Meaning in this policy"),
            [
                (
                    "Original purchaser",
                    "The person or business that bought the device new "
                    "from Lumora or an authorized retailer.",
                ),
                (
                    "Authorized retailer",
                    "A seller listed on the Lumora website on the date of purchase.",
                ),
                (
                    "Certified Refurbished",
                    "A device inspected, repaired if needed and "
                    "re-certified by Lumora, sold with a refurbished warranty.",
                ),
            ],
            widths=(1.5, 3.7),
            caption="Table 1-1. Definitions.",
        ),
        h2("1.2 Warranty Periods"),
        p(
            'Lumora Home Systems, Inc. ("Lumora") warrants that each new Lumora device '
            "will be free from defects in materials and workmanship under normal "
            "residential use for the period shown below."
        ),
        table(
            ("Product", "Standard term", "With certified installation", "Certified Refurbished"),
            [
                ("Thermostat T2 (LT-T2)", "2 years", "2 years (no extension)", "12 months"),
                ("Thermostat T3 (LT-T3)", "3 years", "4 years (see section 5)", "12 months"),
                ("Room Sensor S1 (LS-S1)", "1 year", "Not applicable", "6 months"),
                ("Hub H1 (LH-H1)", "2 years", "Not applicable", "12 months"),
                ("Power Extender Kit PEK-1", "1 year", "1 year", "Not sold refurbished"),
            ],
            widths=(1.6, 1.0, 1.5, 1.2),
            caption="Table 1-2. Warranty periods by product.",
        ),
        note(
            "The T3 internal rechargeable battery is covered for 12 months from the start "
            "of coverage, not for the full 3-year term of the thermostat. A battery that "
            "holds less than 50% of its original capacity within the first 12 months is "
            "considered defective.",
            label="Battery coverage",
        ),
        h1("2. Start and Duration of Coverage"),
        p(
            "Coverage starts on the date the device is delivered to the original purchaser. "
            "If the delivery date cannot be established, coverage starts 5 days after the "
            "purchase date shown on the proof of purchase. Repairs or replacements do not "
            "restart the warranty period. A replacement device is covered for the remainder "
            "of the original warranty period or 90 days from its delivery, whichever is "
            "longer."
        ),
        h1("3. What Lumora Will Do"),
        p(
            "If a covered defect is reported during the warranty period, Lumora will, at "
            "its option, (a) repair the device, (b) replace it with a new or Certified "
            "Refurbished device of the same or a newer model with equal or better "
            "functionality, or (c) refund the purchase price paid. These remedies are the "
            "customer's sole and exclusive remedies under this warranty."
        ),
        h1("4. Exclusions"),
        p("This warranty does not cover:"),
        bullets(
            "Damage caused by connecting a device to line-voltage (120 V or 240 V) wiring, "
            "or by any wiring that does not follow the product guide.",
            "Damage from liquid, fire, lightning, power surges, accidents, abuse, pets or pests.",
            "Cosmetic damage such as scratches and dents that does not affect operation.",
            "Devices bought from sellers that are not Lumora or an authorized retailer "
            "listed on the Lumora website.",
            "Devices whose serial number has been removed, altered or made illegible.",
            "Consumables, including the Room Sensor S1 coin cell battery.",
            "Devices that have been opened, modified or repaired by anyone other than Lumora.",
        ),
        h2("4.1 Commercial Use"),
        p(
            "Devices installed in commercial premises (offices, shops, rental units "
            "managed by a business with more than four units) are covered for 1 year from "
            "delivery, regardless of the standard term in Table 1-2."
        ),
        h1("5. Certified Installation Extension (Thermostat T3)"),
        p(
            "A Thermostat T3 installed by a Lumora Certified Installer receives a 12-month "
            "warranty extension, for a total coverage of 4 years from delivery. The "
            "extension applies only when all of the following conditions are met:"
        ),
        bullets(
            "The installer appears in the Lumora Certified Installer directory on the date "
            "of installation.",
            "The installation is registered in the Lumora Home app, with the installer ID, "
            "within 60 days of installation. Registrations after 60 days are not "
            "accepted, even if the installer was certified.",
            "The installation record, including the pre-installation wiring photo, is "
            "attached to the registration.",
            "The thermostat is installed in a residential property (section 4.1 does not apply).",
        ),
        p(
            "The extension is not available for the Thermostat T2, the Room Sensor S1 or "
            "the Hub H1, and it does not extend the 12-month coverage of the T3 battery. "
            "If a T3 covered by the extension is replaced, the replacement keeps the "
            "extended end date."
        ),
        h1("6. Transfer of Warranty"),
        p(
            "The warranty may be transferred once, to the next owner of the home in which "
            "the device is installed. The new owner must submit the transfer request in the "
            "Lumora Home app within 30 days of taking ownership of the home. Transfers are "
            "not available for devices that were removed from the original home. Lumora "
            "Plus subscriptions and their benefits are not transferable."
        ),
        page_break(),
        h1("7. Coverage Examples"),
        p(
            "The following examples illustrate how the terms above apply. They are "
            "informative; the terms in sections 1 to 6 prevail."
        ),
        table(
            ("Example", "Covered?", "Explanation"),
            [
                (
                    "T3 delivered March 1, 2026, installed by a certified installer on March "
                    "10 and registered on April 2",
                    "Yes, until March 1, 2030",
                    "Registered within 60 days; 4 years from delivery.",
                ),
                (
                    "Same T3, registered on June 15",
                    "Yes, until March 1, 2029",
                    "Registration too late; standard 3-year term.",
                ),
                (
                    "T2 installed by a certified installer",
                    "2 years only",
                    "The extension applies to the T3 only.",
                ),
                (
                    "Hub H1 used in a dental office",
                    "1 year",
                    "Commercial use clause (section 4.1).",
                ),
                ("S1 coin cell battery empty after 18 months", "No", "Batteries are consumables."),
                (
                    "Thermostat replaced 2 months before its warranty ended",
                    "Yes, 90 days",
                    "Replacement covered for the longer of the remainder or 90 days.",
                ),
            ],
            widths=(2.3, 1.2, 1.9),
            caption="Table 7-1. Coverage examples.",
        ),
        h1("8. How to Make a Claim"),
        p(
            "Customers make a claim by contacting Lumora Customer Care by phone, chat or "
            "through the Lumora Home app before the warranty period ends. The customer must "
            "provide the device serial number and, if the device is not registered to their "
            "account, proof of purchase. Lumora may ask the customer to complete basic "
            "troubleshooting before a claim is accepted. Lumora pays shipping for approved "
            "warranty replacements within the United States."
        ),
        h1("9. Limitation of Liability"),
        p(
            "To the extent permitted by law, Lumora is not liable for indirect, incidental "
            "or consequential damages, including damage to HVAC equipment, frozen pipes or "
            "energy costs, arising from the use of or inability to use a device. Lumora's "
            "total liability under this warranty is limited to the purchase price paid for "
            "the device."
        ),
        h1("10. Your Rights Under Law"),
        p(
            "This warranty gives the customer specific legal rights, and the customer may "
            "also have other rights that vary by state. Some states do not allow "
            "limitations on implied warranties or the exclusion of incidental or "
            "consequential damages, so the limitations above may not apply. Nothing in this "
            "policy limits rights that cannot be limited by law."
        ),
        h1("11. Contact"),
        p(
            "Questions about this policy from employees should be sent to the Legal and "
            "Compliance team through the internal service portal. Customer questions are "
            "answered by Customer Care using the published summary of this policy."
        ),
        h1("12. Revision History"),
        table(
            ("Revision", "Effective", "Change"),
            [
                (
                    "2026.1",
                    "January 1, 2026",
                    "Certified installation extension limited to "
                    "the T3; T3 battery coverage clarified.",
                ),
                ("2025.2", "July 1, 2025", "Commercial use clause added."),
                ("2025.1", "January 1, 2025", "Hub H1 term increased to 2 years."),
            ],
            widths=(0.8, 1.2, 3.2),
        ),
    ),
    facts=(
        fact(
            "POL-01",
            "A Thermostat T3 installed by a Lumora Certified Installer gets a 12-month "
            "extension (4 years total), only if registered in the app with the installer ID "
            "within 60 days of installation and other conditions are met.",
            "receives a 12-month warranty extension",
            "within 60 days of installation",
            kind="cross-page",
            tags=("confusable",),
        ),
        fact(
            "POL-02",
            "The T3 internal rechargeable battery is covered for 12 months, not the full "
            "3-year thermostat term.",
            "The T3 internal rechargeable battery is covered for 12 months",
            tags=("confusable",),
        ),
        fact(
            "POL-03",
            "Warranty coverage starts on the delivery date; if unknown, 5 days after the "
            "purchase date.",
            "coverage starts 5 days after the purchase date",
        ),
        fact(
            "POL-04",
            "A replacement device is covered for the remainder of the original warranty or "
            "90 days from its delivery, whichever is longer.",
            "or 90 days from its delivery, whichever is longer",
        ),
        fact(
            "POL-05",
            "Devices installed in commercial premises are covered for 1 year from delivery "
            "regardless of the standard term.",
            "are covered for 1 year from delivery, regardless of the standard term",
        ),
        fact(
            "POL-06",
            "The warranty can be transferred once to the next homeowner, who must request "
            "the transfer within 30 days of taking ownership.",
            "within 30 days of taking ownership of the home",
        ),
        fact(
            "POL-07",
            "Certified Refurbished Room Sensor S1 units have a 6-month warranty.",
            "Room Sensor S1 (LS-S1)",
            kind="table",
        ),
        fact(
            "POL-08",
            "Lumora's total liability under the warranty is limited to the purchase price "
            "paid for the device.",
            "limited to the purchase price paid",
        ),
    ),
)
