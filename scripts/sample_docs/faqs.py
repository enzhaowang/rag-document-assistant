"""FAQs: billing and subscriptions, shipping and delivery, app and account."""

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

# ------------------------------------------------------------------ billing

BILLING_FAQ = SampleDoc(
    filename="FAQ - Billing and Subscriptions.pdf",
    title="Billing and Subscriptions FAQ",
    doc_type="faq",
    doc_number="LHS-FAQ-BIL-003",
    revision="6.0",
    effective_date="March 1, 2026",
    owner="Customer Care Knowledge Team",
    audience="Customer Care agents; approved answers may be shared with customers",
    purpose=(
        "Approved answers to common questions about payments, invoices, price matching "
        "and the Lumora Plus subscription. Answers can be read or pasted to customers as "
        "written."
    ),
    blocks=(
        h1("1. Payments and Invoices"),
        h2("Q1. Which payment methods does Lumora accept?"),
        p(
            "The online store accepts major credit and debit cards, Lumora gift cards and "
            "store credit. Phone orders accept cards only. Lumora does not accept cash on "
            "delivery, checks or bank transfers for consumer orders. Business accounts can "
            "be invoiced with net-30 payment terms after a credit check."
        ),
        h2("Q2. When is my card charged?"),
        p(
            "Cards are authorized when the order is placed and charged when the order "
            "ships. If an order ships in several packages, each package is charged "
            "separately when it ships. Authorizations for items that are cancelled before "
            "shipping are released by the card issuer, usually within 5 business days."
        ),
        h2("Q3. Where can I find my invoice?"),
        p(
            "Invoices for orders and subscriptions are available in the Lumora Home app "
            "under Account > Billing > Invoices, and on the website under Order History. "
            "Each invoice can be downloaded as a PDF. Agents can resend an invoice from "
            "OMS, but cannot change the billing name or address on an invoice that has "
            "already been issued."
        ),
        h2("Q4. Why was I charged sales tax?"),
        p(
            "Sales tax is calculated from the shipping address, not the billing address, "
            "and includes state and local taxes where Lumora is required to collect them. "
            "Tax-exempt organizations must upload their exemption certificate before "
            "ordering; tax already charged is not refunded retroactively."
        ),
        h1("2. Price Match and Promotions"),
        h2("Q5. Does Lumora price match?"),
        p(
            "Yes. If the customer finds a lower advertised price for the same new product "
            "from Lumora or an authorized retailer within 14 days of their purchase, Lumora "
            "refunds the difference. The lower price must be publicly available, in stock "
            "and from a seller located in the United States. Price matching is limited to "
            "one adjustment per order and does not apply to marketplace sellers, open-box "
            "or refurbished offers, bundles, or prices that require a membership."
        ),
        h2("Q6. Can I combine promotion codes?"),
        p(
            "Only one promotion code can be used per order. Promotion codes cannot be "
            "applied to gift card purchases or to Lumora Plus subscriptions, and they "
            "cannot be added after the order has been placed."
        ),
        h2("Q6a. Is there a referral program?"),
        p(
            "Yes. Customers can share a referral link from Account > Refer a Friend. The "
            "friend receives $15 off a first order of $100 or more, and the referring "
            "customer receives $15 in store credit once the friend's order has passed the "
            "30-day return window. Each customer can earn referral credit for up to 10 "
            "referrals per calendar year."
        ),
        h2("Q6b. Does Lumora offer discounts for military, students or seniors?"),
        p(
            "Lumora does not offer group discounts at this time. Agents should not create "
            "manual discounts for these requests; instead, mention any current public "
            "promotion and the price match policy."
        ),
        page_break(),
        h1("3. Lumora Plus Subscription"),
        h2("Q7. What is Lumora Plus and how much does it cost?"),
        p(
            "Lumora Plus is an optional subscription that adds extended history, advanced "
            "energy reports and premium support benefits. It costs $4.99 per month or "
            "$49.00 per year. One subscription covers all devices in one home."
        ),
        table(
            ("Feature", "Free", "Lumora Plus"),
            [
                ("Remote control and schedules", "Included", "Included"),
                ("Temperature and runtime history", "90 days", "3 years"),
                (
                    "Energy reports",
                    "Monthly summary",
                    "Monthly report with room-by-room breakdown and savings tips",
                ),
                ("Advance replacement under warranty", "T3 and H1 only", "All devices"),
                ("Support", "Standard queue", "Priority phone queue"),
                ("Household members", "Up to 8", "Up to 8"),
            ],
            widths=(1.8, 1.2, 2.0),
            caption="Table 3-1. Free plan compared with Lumora Plus.",
        ),
        h2("Q8. Is there a free trial?"),
        p(
            "Customers who activate a new Thermostat T3 receive a 30-day free trial of "
            "Lumora Plus. The trial starts automatically when the T3 is added to the app "
            "and converts to the monthly plan at the end of the trial unless the customer "
            "cancels. Only one trial is available per home, even if several thermostats "
            "are installed. T2 purchases do not include a trial."
        ),
        h2("Q9. What happens if a subscription payment fails?"),
        p(
            "If a renewal payment fails, Lumora retries the card three times over 7 days "
            "and emails the customer after each attempt. If all retries fail, the "
            "subscription is paused and the home moves to the free plan. History beyond "
            "the free limit is kept for 60 days after the pause; if the customer updates "
            "the payment method within those 60 days, Lumora Plus resumes with the full "
            "history."
        ),
        h2("Q10. How do I cancel, and will I get a refund?"),
        p(
            "Customers can cancel at any time in the app under Account > Billing > Lumora "
            "Plus, or by asking an agent. Monthly plans are not refunded; the service "
            "continues until the end of the current month. Annual plans cancelled within "
            "30 days of the start or renewal date receive a full refund. Annual plans "
            "cancelled after 30 days are not refunded, and the service continues until "
            "the end of the paid year."
        ),
        h2("Q11. Can I switch between monthly and annual billing?"),
        p(
            "Yes. Switching from monthly to annual takes effect immediately, and the unused "
            "part of the current month is credited. Switching from annual to monthly takes "
            "effect at the next renewal date."
        ),
        h1("4. Gift Cards and Store Credit"),
        h2("Q12. Do gift cards or store credit expire?"),
        p(
            "Lumora gift cards do not expire and have no fees. Store credit issued for "
            "refunds or goodwill credits expires 24 months after it is issued. Neither can "
            "be exchanged for cash, except where required by state law."
        ),
        h2("Q13. Can store credit pay for Lumora Plus?"),
        p(
            "Store credit and gift cards can be used for products and the first payment of "
            "an annual Lumora Plus plan. Monthly plans and renewals must be paid by card."
        ),
        h1("5. Business Accounts"),
        h2("Q13a. How do business accounts work?"),
        p(
            "Businesses such as installers and property managers can apply for a business "
            "account on the Lumora website. Approval takes up to 3 business days. Business "
            "accounts get volume pricing on orders of 10 or more units of the same product, "
            "free standard shipping, and optional invoicing with net-30 terms after a "
            "credit check. Invoices not paid within 30 days put new orders on hold."
        ),
        table(
            ("Units of the same product per order", "Discount from list price"),
            [
                ("10-24", "8%"),
                ("25-99", "12%"),
                ("100 or more", "Quote from the business sales team"),
            ],
            widths=(2.5, 2.5),
            caption="Table 5-1. Business volume pricing.",
        ),
        h1("6. Billing Disputes"),
        h2("Q14. I see a charge I do not recognize."),
        p(
            "Ask the customer for the date and amount of the charge and search OMS by the "
            "last four digits of the card. Charges usually match a shipped package, a "
            "Lumora Plus renewal or a missed installation appointment fee. If no matching "
            "order is found, advise the customer to contact their card issuer and record "
            "the contact in the ticket."
        ),
        h2("Q15. The customer has filed a chargeback."),
        p(
            "Do not issue a refund or replacement while a chargeback is open. Route the "
            "ticket to the Finance Disputes queue, which responds to the card issuer within "
            "the issuer's deadline. Lumora Plus is suspended while a chargeback for a "
            "subscription payment is open."
        ),
    ),
    facts=(
        fact(
            "FAQ-BIL-01",
            "Lumora Plus costs $4.99 per month or $49.00 per year and covers all devices "
            "in one home.",
            "It costs $4.99 per month or $49.00 per year.",
        ),
        fact(
            "FAQ-BIL-02",
            "Price match: Lumora refunds the difference if a lower price from Lumora or an "
            "authorized retailer is found within 14 days of purchase; one adjustment per "
            "order.",
            "within 14 days of their purchase",
        ),
        fact(
            "FAQ-BIL-03",
            "If a Lumora Plus payment fails, Lumora retries three times over 7 days, then "
            "pauses the subscription.",
            "retries the card three times over 7 days",
        ),
        fact(
            "FAQ-BIL-04",
            "Annual Lumora Plus plans cancelled within 30 days of start or renewal get a "
            "full refund; monthly plans are not refunded.",
            "Annual plans cancelled within 30 days of the start or renewal date",
        ),
        fact(
            "FAQ-BIL-05",
            "New Thermostat T3 customers get a 30-day free trial of Lumora Plus (one per "
            "home); T2 purchases do not include a trial.",
            "T2 purchases do not include a trial.",
            tags=("confusable",),
        ),
        fact(
            "FAQ-BIL-06",
            "Free plan history is kept for 90 days; Lumora Plus keeps 3 years of history.",
            "Temperature and runtime history",
            kind="table",
        ),
        fact(
            "FAQ-BIL-07",
            "Store credit expires 24 months after it is issued; gift cards do not expire.",
            "expires 24 months after it is issued",
        ),
        fact(
            "FAQ-BIL-08",
            "Sales tax is calculated from the shipping address, not the billing address.",
            "Sales tax is calculated from the shipping address",
        ),
    ),
)

# ----------------------------------------------------------------- shipping

SHIPPING_FAQ = SampleDoc(
    filename="FAQ - Shipping and Delivery.pdf",
    title="Shipping and Delivery FAQ",
    doc_type="faq",
    doc_number="LHS-FAQ-SHP-002",
    revision="4.1",
    effective_date="February 2, 2026",
    owner="Customer Care Knowledge Team",
    audience="Customer Care agents; approved answers may be shared with customers",
    purpose=(
        "Approved answers to questions about shipping options, costs, delivery times, "
        "tracking and lost or damaged packages for orders placed on the Lumora online "
        "store or by phone."
    ),
    blocks=(
        h1("1. Shipping Options and Costs"),
        h2("Q1. What shipping options are available?"),
        table(
            ("Method", "Delivery time after shipping", "Cost"),
            [
                ("Standard", "3-5 business days", "$6.95; free on orders over $75"),
                ("Expedited", "2 business days", "$14.95"),
                ("Overnight", "Next business day", "$29.95"),
            ],
            widths=(1.2, 2.0, 2.0),
            caption="Table 1-1. Shipping methods for the contiguous United States.",
        ),
        p(
            "Order totals for the free shipping threshold are calculated after discounts "
            "and before tax. Orders to Alaska and Hawaii ship by expedited service only, "
            "at the expedited rate, and take 3-6 business days."
        ),
        h2("Q2. When will my order ship?"),
        p(
            "Orders placed before 2:00 PM Eastern on a business day ship the same day. "
            "Orders placed later, or on weekends and holidays, ship the next business day. "
            "Overnight orders must be placed before 1:00 PM Eastern to ship the same day. "
            "Orders that include professional installation ship so that the device arrives "
            "at least 2 business days before the appointment."
        ),
        h2("Q3. Where does Lumora ship?"),
        p(
            "Lumora ships to all 50 US states and Washington, D.C. Lumora does not ship "
            "internationally or to freight forwarders. Standard shipping can be delivered "
            "to PO boxes and military APO/FPO addresses; expedited and overnight shipping "
            "cannot."
        ),
        h2("Q4. Is a signature required?"),
        p(
            "A signature is required for orders with a total over $500. Customers cannot "
            "waive the signature requirement. If nobody is available, the carrier makes "
            "two more attempts and then holds the package at a local pickup location for "
            "5 business days before returning it to Lumora."
        ),
        h1("2. Tracking and Changes"),
        h2("Q5. How do I track my order?"),
        p(
            "A shipping confirmation email with the tracking number is sent when each "
            "package leaves the warehouse. Tracking information can take up to 24 hours to "
            "appear in the carrier system. Orders can also be tracked in the app under "
            "Account > Orders."
        ),
        h2("Q6. Can I change the address or cancel my order?"),
        p(
            "The shipping address can be changed and the order can be cancelled within 1 "
            "hour of placing it, in Order History or by contacting Customer Care. After 1 "
            "hour the order is released to the warehouse and cannot be changed; the "
            "customer can refuse the delivery or return the items under the Returns and "
            "Refunds SOP. Agents cannot redirect packages that are already in transit."
        ),
        h2("Q6a. Can I pick up my order?"),
        p(
            "No. Lumora does not have retail stores or pickup locations. Customers who "
            "need a product the same day can check authorized retailers listed on the "
            "Lumora website; those purchases are covered by the retailer's return policy."
        ),
        h2("Q6b. Can I ship to a different address than my billing address?"),
        p(
            "Yes. Orders over $1,000 shipped to an address different from the billing "
            "address may be held for up to 1 business day for a fraud review. The customer "
            "is contacted by email if more information is needed."
        ),
        h1("3. Problems With Deliveries"),
        h2("Q7. My tracking has not updated for several days. What should I do?"),
        p(
            "If tracking shows no movement for 5 business days, the agent opens a carrier "
            "trace in OMS. Lumora ships a free replacement by expedited shipping if the "
            "trace confirms the package is lost, or if the trace has no result after 3 "
            "more business days. The customer does not need to wait for the carrier to "
            "finish its investigation."
        ),
        h2("Q8. Tracking says delivered, but I do not have the package."),
        p(
            "Ask the customer to check with neighbors and around the property, and to wait "
            "until the end of the next business day because carriers sometimes mark "
            "packages as delivered early. Missing deliveries must be reported within 7 "
            "days of the delivery scan. For the first report on an account, Lumora ships a "
            "replacement at no cost. For any further report within 12 months, the customer "
            "must file a police report before a replacement is approved by a Team Lead."
        ),
        h2("Q9. My package arrived damaged."),
        p(
            "Customers should take photos of the box and the product and contact Customer "
            "Care within 7 days of delivery. The agent creates a return with reason code "
            "DT-04 and ships a replacement as soon as the photos are received; the damaged "
            "item must be returned with the prepaid label."
        ),
        note(
            "If the device itself shows signs of damage such as a cracked display or "
            "exposed electronics, tell the customer not to install or power it.",
            label="Safety",
        ),
        h2("Q10. Part of my order is missing."),
        p(
            "Large orders may ship in more than one package; check the shipping "
            "confirmation emails first. If an item is missing from a package that has "
            "arrived, the agent checks the package weight recorded by the warehouse in "
            "OMS. If the recorded weight matches a complete shipment, the case is "
            "escalated to the warehouse for review within 2 business days before a "
            "replacement is sent."
        ),
        h1("4. Holidays and Installation Appointments"),
        h2("Q11. What are the holiday shipping cutoffs?"),
        p(
            "Lumora publishes the exact cutoff dates on the website each November. As a "
            "rule, standard orders must be placed by December 15 and expedited orders by "
            "December 20 to arrive before December 25. Overnight orders placed by 1:00 PM "
            "Eastern on December 23 arrive on December 24. The warehouse is closed on "
            "Thanksgiving Day, December 25 and January 1."
        ),
        h2("Q12. How are installation appointments scheduled?"),
        p(
            "When an order includes professional installation, the customer receives a "
            "scheduling link by email after the order ships. Appointments are available "
            "Monday to Saturday in 3-hour arrival windows. Customers can reschedule "
            "without charge up to 24 hours before the appointment; a missed appointment "
            "without notice incurs a $49 fee deducted from the installation refund."
        ),
        h2("Q13. What packaging does Lumora use?"),
        p(
            "Orders ship in recyclable cardboard with paper padding. Lumora does not use "
            "plastic air pillows or foam. Several items in one order may be packed together "
            "in one box to reduce waste, even when they appear as separate lines on the "
            "invoice."
        ),
        h1("5. Business and Bulk Orders"),
        bullets(
            "Orders of 25 or more units ship by freight and require a delivery appointment.",
            "Business accounts receive standard shipping free on all orders.",
            "Freight deliveries must be inspected on arrival and damage noted on the "
            "delivery receipt; otherwise damage claims cannot be accepted.",
        ),
        h1("6. Return Shipping"),
        h2("Q14. How do I send a return back?"),
        p(
            "Every approved return or warranty RMA comes with a prepaid return label sent "
            "by email. The customer prints the label, attaches it to the box and drops the "
            "package at any location of the carrier named on the label, or schedules a "
            "free pickup from the carrier website. Customers without a printer can show "
            "the QR code from the email at a staffed carrier location."
        ),
        h2("Q15. Do I need the original box?"),
        p(
            "No. Any sturdy box works as long as the device is padded and cannot move. "
            "Customers should not tape the label over old barcodes; old labels must be "
            "removed or fully covered."
        ),
        h2("Q16. How long does a return take to reach Lumora?"),
        p(
            "Return packages usually take 3-7 business days to reach the Returns "
            "Processing Center. The customer can follow the tracking link in the RMA "
            "email. Refunds and replacements start after the RPC has received and "
            "inspected the package, as described in the Returns and Refunds SOP."
        ),
    ),
    facts=(
        fact(
            "FAQ-SHP-01",
            "Standard shipping costs $6.95 and takes 3-5 business days; it is free on orders "
            "over $75.",
            "$6.95; free on orders over $75",
            kind="table",
        ),
        fact(
            "FAQ-SHP-02",
            "Expedited shipping costs $14.95 (2 business days) and overnight costs $29.95.",
            "$29.95",
            kind="table",
        ),
        fact(
            "FAQ-SHP-03",
            "Orders placed before 2:00 PM Eastern on a business day ship the same day; "
            "overnight orders must be placed before 1:00 PM Eastern.",
            "Orders placed before 2:00 PM Eastern on a business day ship the same day.",
        ),
        fact(
            "FAQ-SHP-04",
            "A signature is required for orders over $500 and cannot be waived.",
            "A signature is required for orders with a total over $500.",
        ),
        fact(
            "FAQ-SHP-05",
            "Orders can be changed or cancelled within 1 hour of placing them.",
            "cancelled within 1 hour of placing it",
        ),
        fact(
            "FAQ-SHP-06",
            "If tracking shows no movement for 5 business days, the agent opens a carrier "
            "trace; a free expedited replacement ships if the package is lost or the trace "
            "has no result after 3 more business days.",
            "If tracking shows no movement for 5 business days",
        ),
        fact(
            "FAQ-SHP-07",
            "Missing deliveries must be reported within 7 days of the delivery scan; a "
            "second report within 12 months requires a police report.",
            "within 7 days of the delivery scan",
        ),
        fact(
            "FAQ-SHP-08",
            "Lumora ships to all 50 US states and Washington, D.C., and does not ship "
            "internationally; expedited and overnight cannot go to PO boxes.",
            "Lumora does not ship internationally",
        ),
        fact(
            "FAQ-SHP-09",
            "Orders of 25 or more units ship by freight and require a delivery appointment.",
            "Orders of 25 or more units ship by freight",
        ),
    ),
)

# --------------------------------------------------------------------- app

APP_ACCOUNT_FAQ = SampleDoc(
    filename="FAQ - App and Account.pdf",
    title="App and Account FAQ",
    doc_type="faq",
    doc_number="LHS-FAQ-APP-005",
    revision="3.4",
    effective_date="April 6, 2026",
    owner="Customer Care Knowledge Team",
    audience="Customer Care agents; approved answers may be shared with customers",
    purpose=(
        "Approved answers to questions about the Lumora Home app, account security, "
        "household sharing, data and privacy, and app features such as Away mode and "
        "energy reports."
    ),
    blocks=(
        h1("1. Account and Sign-In"),
        h2("Q1. What are the password requirements?"),
        p(
            "Passwords must be at least 10 characters long and include at least one letter "
            "and one number. Passwords used in known data breaches are rejected. The app "
            "never asks for the password by email, and agents must never ask customers for "
            "their password."
        ),
        h2("Q2. I am locked out of my account."),
        p(
            "After 5 failed sign-in attempts the account is locked for 15 minutes. After "
            "the lock expires the customer can try again or use Forgot Password. Password "
            "reset links are valid for 1 hour. Agents cannot unlock accounts manually."
        ),
        h2("Q3. How does two-step verification work?"),
        p(
            "Two-step verification can use an authenticator app or a text message code. "
            "It is optional for most users but mandatory for the home Owner when the home "
            "has more than 3 members. If the customer loses access to their second step, "
            "they can use one of the 10 recovery codes shown at setup. Without recovery "
            "codes, identity must be verified by Tier 2 using the order history, which "
            "takes up to 2 business days."
        ),
        h2("Q4. How do I change my email address?"),
        p(
            "The email address is changed in Account > Profile. A verification link is sent "
            "to the new address and is valid for 24 hours; the change only takes effect "
            "after the link is opened. A notice is also sent to the old address."
        ),
        h1("2. Household Sharing"),
        h2("Q5. Can other people in my home use the app?"),
        p(
            "Yes. The Owner can invite up to 8 household members per home. Each member has "
            "one of three roles:"
        ),
        table(
            ("Role", "Permissions"),
            [
                (
                    "Owner",
                    "Everything, including billing, deleting the home and transferring "
                    "ownership. Each home has exactly one Owner.",
                ),
                (
                    "Admin",
                    "Add and remove devices, change schedules and settings, invite "
                    "Members. Cannot manage billing or remove the Owner.",
                ),
                (
                    "Member",
                    "Change temperatures and use Away mode. Cannot change schedules, "
                    "devices or other members.",
                ),
            ],
            widths=(0.9, 4.0),
            caption="Table 2-1. Household roles.",
        ),
        p(
            "Invitations expire after 7 days. Members can leave a home at any time; the "
            "Owner must transfer ownership to an Admin before leaving."
        ),
        h2("Q5a. Can I give temporary access to a guest or a babysitter?"),
        p(
            "Yes. Owners and Admins can create guest access in Settings > Members > Guest. "
            "Guests have the same permissions as Members but their access expires "
            "automatically after the end date chosen by the Owner, at most 30 days later. "
            "Guests do not count toward the limit of 8 household members."
        ),
        h2("Q5b. How do I remove a household member?"),
        p(
            "Owners and Admins can remove Members in Settings > Members. Only the Owner can "
            "remove an Admin. Removed members are signed out of the home immediately but "
            "keep their own Lumora account."
        ),
        page_break(),
        h1("3. App Features"),
        h2("Q6. How does Away mode work?"),
        p(
            "Away mode uses the location of household members' phones to detect when "
            "everyone has left. The home switches to the Away temperatures when all "
            "members with location sharing turned on are outside the geofence, and back "
            "when the first member returns. The default geofence radius is 500 m (about "
            "0.3 mi) and can be set between 150 m and 3,000 m in Settings > Away."
        ),
        h2("Q7. When are energy reports sent?"),
        p(
            "Energy reports for the previous month are sent by email and shown in the app "
            "on the 3rd day of each month. Reports need at least 20 days of data in the "
            "month; homes set up later in the month receive their first report the "
            "following month."
        ),
        h2("Q8. Does the app work without internet?"),
        p(
            "The app needs an internet connection to control devices remotely. Homes with "
            "a Hub H1 can still be controlled from a phone on the same local network when "
            "the internet is down. Thermostats always keep running their schedules without "
            "internet."
        ),
        h1("4. Data and Privacy"),
        h2("Q9. How long is my data kept?"),
        p(
            "Temperature and runtime history is kept for 90 days on the free plan and for "
            "3 years with Lumora Plus. Location data used for Away mode is processed on "
            "the phone and only the result (home or away) is sent to Lumora; it is kept "
            "for 30 days."
        ),
        h2("Q10. How do I delete my account?"),
        p(
            "The Owner can request deletion in Account > Privacy > Delete Account. Devices "
            "must be removed from the home first. The account is deactivated immediately "
            "and permanently deleted after 30 days; during those 30 days, signing in "
            "again cancels the deletion. Order and invoice records are kept for 7 years "
            "because of tax requirements, even after the account is deleted."
        ),
        h2("Q11. Can I download my data?"),
        p(
            "Yes. In Account > Privacy > Download My Data the customer can request an "
            "export of account, device and history data. The download link is emailed "
            "within 72 hours and is valid for 7 days."
        ),
        page_break(),
        h1("5. Homes, Devices and Updates"),
        h2("Q12. Can I manage more than one home?"),
        p(
            "Yes. One account can own or be a member of up to 5 homes, for example a main "
            "residence and a vacation home. Each home has its own devices, members, "
            "schedules and Lumora Plus subscription. Switch homes from the home name at "
            "the top of the app."
        ),
        h2("Q13. How are device firmware updates handled?"),
        p(
            "Firmware updates are installed automatically. Thermostats update overnight "
            "when idle, and the Hub H1 updates between 2:00 and 4:00 AM local time. The "
            "app shows the current version of each device under Device > About and "
            "notifies the Owner when an update has been installed. Customers cannot "
            "install older firmware versions."
        ),
        h2("Q14. Can I use the app on a tablet or computer?"),
        p(
            "The Lumora Home app runs on phones and tablets. A web dashboard at the Lumora "
            "website offers schedules, history and energy reports from a computer, but "
            "device setup and Away mode require the mobile app."
        ),
        h2("Q15. What happens when I sell my home?"),
        p(
            "The Owner should transfer the home to the buyer in Account > Homes > Transfer "
            "Home, or remove all devices from the account before moving out. The buyer can "
            "then add the devices to their own account. Warranty transfer is a separate "
            "request described in the Lumora Limited Warranty Policy."
        ),
        h2("Q16. Which notifications does the app send?"),
        table(
            ("Notification", "Default", "Can be turned off?"),
            [
                ("Device offline for more than 30 minutes", "On", "Yes"),
                ("Indoor temperature below 45 °F or above 95 °F", "On", "No"),
                ("Low battery (S1 or T3)", "On", "Yes"),
                ("Filter reminder", "Every 90 days", "Yes; interval 30-180 days"),
                ("Firmware update installed", "On", "Yes"),
                ("Monthly energy report ready", "On", "Yes"),
            ],
            widths=(2.4, 1.2, 1.5),
            caption="Table 5-1. App notifications.",
        ),
        p(
            "Extreme temperature alerts cannot be turned off because they can indicate a "
            "heating or cooling failure that may damage the home, such as frozen pipes. "
            "They are sent to the Owner and all Admins."
        ),
        h1("6. Troubleshooting the App"),
        bullets(
            "**Devices show offline in the app but work on the wall:** check the home "
            "network; see the product guide error codes (E4 on the T2, E12 on the T3).",
            "**Notifications not arriving:** confirm notifications are allowed for the app "
            "in the phone settings and that the member has not muted the home.",
            "**App crashes on start:** update the app to the latest version. The app "
            "supports the current and the previous major version of each mobile operating "
            "system.",
        ),
        h1("7. Accessibility and Languages"),
        h2("Q17. Which languages does the app support?"),
        p(
            "The app and the thermostat displays support English, Spanish and French. The "
            "app follows the phone language; thermostats are set during setup or under "
            "Settings > Language. Energy reports are sent in the language of the Owner's "
            "app."
        ),
        h2("Q18. Does the app support screen readers and large text?"),
        p(
            "Yes. All app screens support the screen reader and text size settings of the "
            "phone. The thermostat setpoint can be read aloud by double-tapping the "
            "temperature in the app. Customers who have difficulty using the app can ask an "
            "agent to set up schedules on their behalf after verifying their identity."
        ),
    ),
    facts=(
        fact(
            "FAQ-APP-01",
            "After 5 failed sign-in attempts the account is locked for 15 minutes; password "
            "reset links are valid for 1 hour.",
            "After 5 failed sign-in attempts the account is locked for 15 minutes.",
        ),
        fact(
            "FAQ-APP-02",
            "Passwords must be at least 10 characters with at least one letter and one number.",
            "at least 10 characters long",
        ),
        fact(
            "FAQ-APP-03",
            "The Owner can invite up to 8 household members per home; invitations expire "
            "after 7 days.",
            "invite up to 8 household members per home",
        ),
        fact(
            "FAQ-APP-04",
            "A Member role can change temperatures and use Away mode but cannot change "
            "schedules, devices or other members.",
            "Change temperatures and use Away mode.",
            kind="table",
        ),
        fact(
            "FAQ-APP-05",
            "The default Away mode geofence radius is 500 m, adjustable from 150 m to 3,000 m.",
            "The default geofence radius is 500 m",
        ),
        fact(
            "FAQ-APP-06",
            "Energy reports are sent on the 3rd day of each month and require at least 20 "
            "days of data.",
            "on the 3rd day of each month",
        ),
        fact(
            "FAQ-APP-07",
            "Deleted accounts are permanently removed after 30 days; signing in during that "
            "period cancels deletion, and order records are kept for 7 years.",
            "permanently deleted after 30 days",
        ),
        fact(
            "FAQ-APP-08",
            "Two-step verification is mandatory for the home Owner when the home has more "
            "than 3 members.",
            "mandatory for the home Owner when the home has more than 3 members",
        ),
        fact(
            "FAQ-APP-09",
            "Data export download links are emailed within 72 hours and are valid for 7 days.",
            "emailed within 72 hours",
        ),
    ),
)

FAQS = (BILLING_FAQ, SHIPPING_FAQ, APP_ACCOUNT_FAQ)
