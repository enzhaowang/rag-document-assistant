"""Product guides: Thermostat T2, Thermostat T3, Room Sensor S1 and Hub H1."""

from scripts.sample_docs.model import (
    SampleDoc,
    bullets,
    fact,
    h1,
    h2,
    h3,
    note,
    p,
    page_break,
    steps,
    table,
)

_SAFETY_STEPS = (
    "Switch off power to the heating and cooling equipment at the circuit breaker or "
    "service switch. Confirm the system is off by raising the setpoint on the old "
    "thermostat and waiting two minutes; the equipment must not start.",
    "Remove the faceplate of the existing thermostat and take a clear photo of the "
    "wiring before disconnecting anything. Installers must attach this photo to the "
    "installation record.",
    "Label each wire with the supplied wire labels according to the terminal letter it "
    "was connected to, not by wire color. Wire colors are not standardized between "
    "installers.",
    "Disconnect the wires and remove the old wall plate. Wrap the wire bundle around a "
    "pencil so that it cannot fall back into the wall.",
)

# --------------------------------------------------------------------------- T2

THERMOSTAT_T2 = SampleDoc(
    filename="Product Guide - Lumora Thermostat T2.pdf",
    title="Lumora Thermostat T2 Product Guide",
    doc_type="product_guide",
    doc_number="LHS-PG-T2-001",
    revision="3.1",
    effective_date="March 2, 2026",
    owner="Product Support Engineering",
    audience="Customer Care, Technical Support, Certified Installers",
    purpose=(
        "Reference for supporting the Lumora Thermostat T2 (model LT-T2), covering "
        "specifications, installation, configuration, troubleshooting and error codes. "
        "Use this guide together with the Ticket Escalation SOP when a case cannot be "
        "resolved at first contact."
    ),
    blocks=(
        h1("1. Product Overview"),
        p(
            "The Lumora Thermostat T2 is the entry model of the Lumora climate line. It "
            "replaces a standard low-voltage wall thermostat and adds scheduling, remote "
            "control through the Lumora Home app and monthly energy reports. The T2 is "
            "designed for single-zone homes with conventional furnaces, boilers and "
            "single-stage heat pumps."
        ),
        p(
            "The T2 is sold under SKU LT-T2-01 at a list price of $149.00. It is "
            "positioned below the Lumora Thermostat T3, which adds a color touchscreen, a "
            "humidity sensor, multi-stage heat pump support and battery-backed operation. "
            "Agents should take care not to mix up the two models: several limits, error "
            "codes and the warranty term are different."
        ),
        h2("1.1 What Is in the Box"),
        bullets(
            "Thermostat T2 display unit and wall plate",
            "Optional trim plate for covering marks left by older thermostats",
            "Two wall screws, two drywall anchors and a sheet of wire labels",
            "Quick Start card with the pairing code (also printed on the back of the unit)",
        ),
        h2("1.2 System Compatibility"),
        p(
            "The T2 works with 24 VAC low-voltage systems only. It is compatible with gas, "
            "oil and electric furnaces, hot-water and steam boilers, central air "
            "conditioning and single-stage heat pumps without auxiliary heat."
        ),
        p(
            "**The T2 requires a C-wire (24 VAC common) for continuous power.** If the home "
            "has no C-wire, the Lumora Power Extender Kit PEK-1 must be installed at the "
            "equipment control board. The T2 has no internal battery and cannot run on "
            "power-stealing."
        ),
        note(
            "The T2 is not compatible with line-voltage (120 V or 240 V) systems such as "
            "electric baseboard heaters. Thick wires joined with wire nuts at the old "
            "thermostat usually indicate line voltage. Do not proceed with installation "
            "and advise the customer that the product is not suitable.",
            label="Warning",
        ),
        h1("2. Specifications"),
        table(
            ("Item", "Thermostat T2 (LT-T2)"),
            [
                ("Display", "2.8 in monochrome LCD with backlight, push-and-turn control ring"),
                ("Setpoint range", "45 °F to 90 °F (7 °C to 32 °C)"),
                ("Temperature accuracy", "±1.0 °F (±0.5 °C)"),
                ("Humidity sensing", "Not available"),
                (
                    "Supported stages",
                    "Up to 2 heat / 1 cool (conventional); 1-stage heat pump without "
                    "auxiliary heat",
                ),
                ("Power", "24 VAC, 50/60 Hz; C-wire required (or PEK-1 kit)"),
                ("Power consumption", "Max 1.2 W"),
                ("Wireless", "802.11 b/g/n, 2.4 GHz only; LumoraLink radio for sensors"),
                ("Room Sensor S1 support", "Up to 2 sensors"),
                ("Compressor protection", "Fixed 5-minute minimum off-time"),
                ("Clock backup", "Retains time for 48 hours without power"),
                ("Dimensions", "3.9 x 3.9 x 1.1 in (99 x 99 x 28 mm)"),
                ("Operating environment", "32 °F to 104 °F, 5% to 90% RH non-condensing"),
                ("Warranty", "2 years (24 months) limited warranty"),
            ],
            widths=(1.2, 2.8),
            caption="Table 2-1. Thermostat T2 technical specifications.",
        ),
        p(
            "Settings and schedules are stored in non-volatile memory and survive a power "
            "loss of any duration. Only the clock depends on the backup capacitor; after "
            "more than 48 hours without power the T2 resynchronizes its clock from the "
            "network when it reconnects."
        ),
        page_break(),
        h1("3. Installation"),
        p(
            "Installation takes 30 to 45 minutes for most homes. Customers may install the "
            "T2 themselves. Customer Care may offer professional installation through the "
            "Lumora Certified Installer network for a flat fee of $129."
        ),
        h2("3.1 Before You Start"),
        steps(*_SAFETY_STEPS),
        h2("3.2 Wiring Terminals"),
        table(
            ("Terminal", "Function", "Typical wire color"),
            [
                ("R / Rh", "24 VAC power (heating transformer)", "Red"),
                ("Rc", "24 VAC power (cooling transformer); jumper to R if only one", "Red"),
                ("C", "24 VAC common - required for the T2", "Blue or black"),
                ("W1", "Heat stage 1", "White"),
                ("W2", "Heat stage 2", "Brown or white"),
                ("Y1", "Cool stage 1 / compressor", "Yellow"),
                ("G", "Fan", "Green"),
                ("O/B", "Heat pump reversing valve", "Orange or dark blue"),
            ],
            widths=(0.8, 2.4, 1.2),
            caption="Table 3-1. T2 wall plate terminals.",
        ),
        h2("3.3 Mounting and Wiring"),
        steps(
            "Hold the T2 wall plate against the wall with the bubble level at the top, "
            "mark the two screw holes and drill 3/16 in holes if anchors are needed.",
            "Feed the wires through the center opening and screw the wall plate to the wall.",
            "Insert each labelled wire into the matching terminal until the terminal "
            "button clicks. Strip wires to 1/4 in if the copper end is damaged.",
            "Push excess wire back into the wall and snap the display onto the wall plate.",
            "Restore power at the breaker. The T2 starts within 60 seconds and shows the "
            "setup screen.",
        ),
        h2("3.4 Power Extender Kit PEK-1"),
        p(
            "If the customer has no C-wire, the PEK-1 is installed inside the furnace or "
            "air handler and creates a virtual common conductor over the existing wires. "
            "The kit is free of charge for T2 customers who request it within 60 days of "
            "delivery; after that it costs $24.99. Only Tier 2 Technical Support may "
            "authorize a free PEK-1 outside the 60-day window."
        ),
        h1("4. Setup and Configuration"),
        h2("4.1 First-Time Setup"),
        steps(
            "Choose the language and temperature unit on the thermostat.",
            "Select the equipment type: conventional (furnace or boiler) or heat pump.",
            "Connect the T2 to the home wireless network (2.4 GHz only). Networks that use "
            "the same name on 2.4 GHz and 5 GHz work as long as 2.4 GHz is enabled.",
            "Open the Lumora Home app, tap Add Device and enter the six-digit pairing code "
            "from the Quick Start card.",
            "Run the equipment test from Settings > Equipment > Test to confirm heat, cool "
            "and fan each start correctly.",
        ),
        h2("4.2 Schedules and Comfort Settings"),
        p(
            "The T2 supports up to four schedule periods per day (Wake, Away, Home, Sleep) "
            "with separate weekday and weekend programs. Temporary holds last until the "
            "next schedule period; permanent holds stay in place until the customer "
            "cancels them in the app or on the device."
        ),
        p(
            "Auto changeover between heating and cooling requires a minimum deadband of "
            "3 °F between the heat and cool setpoints. The T2 refuses settings that would "
            "make the deadband smaller."
        ),
        h2("4.3 Adding Room Sensors"),
        p(
            "The T2 can average its own reading with up to two Lumora Room Sensor S1 "
            'units. When a third sensor is added the app shows the message "Sensor limit '
            'reached". Customers who need more sensors should be offered the T3, which '
            "supports more sensors."
        ),
        page_break(),
        h1("5. Troubleshooting"),
        p(
            "Always confirm the firmware version (Settings > About) before troubleshooting. "
            "The current release for the T2 is 4.8.2. Devices on 4.6 or earlier must be "
            "updated first because several connection issues were fixed in 4.7."
        ),
        table(
            ("Symptom", "Likely cause", "Resolution"),
            [
                (
                    "Display stays blank after installation",
                    "No 24 VAC on R and C; furnace door switch open; blown 3 A fuse on "
                    "control board",
                    "Check the furnace door is fully closed. Measure R-C voltage. Replace "
                    "the fuse if needed. Escalate to Tier 2 if voltage is present.",
                ),
                (
                    "System short-cycles",
                    "Thermostat mounted near a supply vent or in direct sunlight",
                    "Relocate or increase the cycle rate setting. Compressor off-time is "
                    "fixed at 5 minutes and cannot be lowered.",
                ),
                (
                    "Temperature reads 2-4 °F high",
                    "Heat from a lamp, TV or exterior wall",
                    "Apply a temperature offset of up to ±5 °F in Settings > Sensors.",
                ),
                (
                    "Fan runs constantly",
                    "G wire touching another terminal or fan set to On",
                    "Set fan to Auto; reseat the G wire.",
                ),
                (
                    "App shows device offline",
                    "Router changed or 5 GHz-only network",
                    "Reconnect from Settings > Network; see error E4.",
                ),
            ],
            widths=(1.2, 1.5, 2.0),
            caption="Table 5-1. Common T2 symptoms.",
        ),
        h2("5.1 Factory Reset"),
        p(
            "A factory reset erases schedules, network credentials and the link to the "
            "customer account. To reset the T2, press and hold the control ring for 12 "
            "seconds until the display shows RESET, then release. The device restarts in "
            "setup mode. Agents should only suggest a factory reset after the standard "
            "troubleshooting steps fail, and must note it in the ticket."
        ),
        h1("6. Error Codes"),
        p(
            "Error codes appear in the top-right corner of the display and in the app. "
            "The same code number can mean something different on the T3; always check "
            "the model before looking up a code."
        ),
        table(
            ("Code", "Meaning", "Recommended action"),
            [
                (
                    "E1",
                    "Internal temperature sensor failure",
                    "Power-cycle; if it persists, start a warranty claim.",
                ),
                (
                    "E2",
                    "No heat detected after 20 minutes of heat call",
                    "Check furnace operation and the W1 wire.",
                ),
                (
                    "E3",
                    "No cooling detected after 20 minutes of cool call",
                    "Check Y1 wire and outdoor unit breaker.",
                ),
                (
                    "E4",
                    "Lost connection to the wireless network for more than 10 minutes",
                    "Confirm 2.4 GHz is enabled; reconnect in Settings > Network.",
                ),
                (
                    "E5",
                    "Room sensor not reporting for 2 hours",
                    "Replace the S1 battery or move the sensor closer.",
                ),
                (
                    "E6",
                    "Wall plate contact fault",
                    "Remove and reseat the display on the wall plate.",
                ),
                (
                    "E7",
                    "Low supply voltage: R-C below 18 VAC",
                    "Check C-wire and transformer; install PEK-1 if there is no C-wire.",
                ),
                (
                    "E8",
                    "Firmware update failed",
                    "Device rolls back automatically; retry from the app after 1 hour.",
                ),
                ("E9", "Clock not set after power loss", "Reconnect to the network to sync time."),
            ],
            widths=(0.5, 2.0, 2.0),
            caption="Table 6-1. Thermostat T2 error codes.",
        ),
        page_break(),
        h1("7. Maintenance, Warranty and Support"),
        h2("7.1 Maintenance"),
        p(
            "The T2 needs no routine maintenance. Clean the display with a dry microfiber "
            "cloth; do not spray liquid cleaners on the unit. Firmware updates install "
            "automatically overnight when the thermostat is idle."
        ),
        h2("7.2 Warranty Summary"),
        p(
            "**The Thermostat T2 carries a 2-year (24-month) limited warranty from the "
            "date of delivery.** This is shorter than the T3 warranty. Full terms, "
            "exclusions and the claim procedure are defined in the Lumora Limited Warranty "
            "Policy (LHS-POL-001) and the Warranty Claims SOP (LHS-SOP-TS-007)."
        ),
        h2("7.3 When to Escalate"),
        bullets(
            "Any report of a burning smell, scorch marks or melted terminals: treat as a "
            "safety case and follow the P1 process in the Ticket Escalation SOP.",
            "E1 or E6 that returns after a power-cycle and reseat.",
            "More than one T2 at the same address showing E4 at the same time after a "
            "firmware update.",
        ),
        h1("8. Appendix A: Pre-Sale Compatibility Checklist"),
        p(
            "Customer Care uses this checklist before recommending the T2 to a customer who "
            'has not bought a thermostat yet. If any answer is "No" in the T2 column, '
            "recommend the T3 or a Certified Installer visit instead."
        ),
        table(
            ("Question for the customer", "T2 suitable if", "If not"),
            [
                (
                    "Is the current thermostat connected with thin, low-voltage wires?",
                    "Yes",
                    "Not compatible (line voltage).",
                ),
                (
                    "Is there a wire on the C terminal, or can a PEK-1 be fitted?",
                    "Yes",
                    "Recommend the T3.",
                ),
                (
                    "Does the system have more than 2 heat stages or 1 cool stage?",
                    "No",
                    "Recommend the T3.",
                ),
                (
                    "Is it a heat pump with auxiliary or emergency heat?",
                    "No",
                    "Recommend the T3 with C-wire.",
                ),
                (
                    "Does the customer want more than 2 room sensors?",
                    "No",
                    "Recommend the T3 (up to 6).",
                ),
                ("Does the home network offer 2.4 GHz?", "Yes", "Enable 2.4 GHz or use a Hub H1."),
            ],
            widths=(2.6, 0.9, 1.6),
            caption="Table 8-1. T2 compatibility checklist.",
        ),
        h1("9. Appendix B: Quick Answers for Agents"),
        h3("Can the T2 control a humidifier?"),
        p(
            "No. The T2 has no accessory terminals and no humidity sensor. Customers who "
            "need humidity control should be offered the T3."
        ),
        h3("Does the T2 work during a power outage?"),
        p(
            "No. The heating and cooling equipment does not run without power either. When "
            "power returns, the T2 restarts automatically with its schedule intact."
        ),
        h3("Can two T2 thermostats be used in the same home?"),
        p(
            "Yes, one per zone. Homes with two or more thermostats need a Hub H1 so that the "
            "app can show all zones in one home."
        ),
        h3("Can the T2 lock its controls?"),
        p(
            "Yes. Settings > Lock sets a 4-digit PIN. While locked, the control ring only "
            "shows the current temperature. The PIN can be removed from the app by the home "
            "Owner or an Admin."
        ),
        h3("Why does the display dim?"),
        p(
            "The backlight dims after 30 seconds without interaction to save power. "
            "Brightness and timeout can be changed under Settings > Display."
        ),
        h1("Revision History"),
        table(
            ("Revision", "Date", "Change"),
            [
                ("3.1", "March 2, 2026", "Added PEK-1 free-of-charge window; firmware 4.8.2."),
                ("3.0", "October 14, 2025", "New error codes E8 and E9."),
                ("2.4", "May 5, 2025", "Clarified line-voltage warning."),
            ],
            widths=(0.8, 1.2, 3.0),
        ),
    ),
    facts=(
        fact(
            "PG-T2-01",
            "The Thermostat T2 setpoint range is 45 °F to 90 °F (7 °C to 32 °C).",
            "45 °F to 90 °F (7 °C to 32 °C)",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-02",
            "The T2 requires a C-wire; homes without one need the Power Extender Kit PEK-1. "
            "The T2 has no internal battery and cannot run on power-stealing.",
            "The T2 requires a C-wire (24 VAC common) for continuous power.",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-03",
            "The T2 supports up to 2 Lumora Room Sensor S1 units.",
            "Up to 2 sensors",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-04",
            "On the T2, error E4 means the thermostat lost its wireless network connection "
            "for more than 10 minutes.",
            "Lost connection to the wireless network for more than 10 minutes",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-05",
            "On the T2, error E7 means low supply voltage (R-C below 18 VAC).",
            "Low supply voltage: R-C below 18 VAC",
            kind="table",
        ),
        fact(
            "PG-T2-06",
            "To factory reset a T2, press and hold the control ring for 12 seconds until "
            "the display shows RESET.",
            "press and hold the control ring for 12 seconds",
        ),
        fact(
            "PG-T2-07",
            "The Thermostat T2 has a 2-year (24-month) limited warranty from the date of delivery.",
            "2-year (24-month) limited warranty from the date of delivery",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-08",
            "The PEK-1 kit is free for T2 customers who request it within 60 days of "
            "delivery; afterwards it costs $24.99, and only Tier 2 can authorize a free kit "
            "outside the window.",
            "within 60 days of delivery; after that it costs $24.99",
        ),
        fact(
            "PG-T2-09",
            "The T2 compressor minimum off-time is fixed at 5 minutes and cannot be lowered.",
            "Fixed 5-minute minimum off-time",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T2-11",
            "On the T2, error E8 means a firmware update failed; the device rolls back "
            "automatically and the update can be retried from the app after 1 hour. (This "
            "row is on the continuation page of the T2 error code table.)",
            "Device rolls back automatically; retry from the app after 1 hour.",
            kind="table",
        ),
        fact(
            "PG-T2-10",
            "T2 auto changeover requires a minimum deadband of 3 °F between heat and cool "
            "setpoints.",
            "minimum deadband of 3 °F",
        ),
    ),
)

# --------------------------------------------------------------------------- T3

THERMOSTAT_T3 = SampleDoc(
    filename="Product Guide - Lumora Thermostat T3.pdf",
    title="Lumora Thermostat T3 Product Guide",
    doc_type="product_guide",
    doc_number="LHS-PG-T3-001",
    revision="2.2",
    effective_date="April 20, 2026",
    owner="Product Support Engineering",
    audience="Customer Care, Technical Support, Certified Installers",
    purpose=(
        "Reference for supporting the Lumora Thermostat T3 (model LT-T3): specifications, "
        "installation including homes without a C-wire, multi-stage and heat pump "
        "configuration, humidity control, troubleshooting and error codes."
    ),
    blocks=(
        h1("1. Product Overview"),
        p(
            "The Lumora Thermostat T3 is the premium model of the Lumora climate line. It "
            "has a 3.5 in color touchscreen, a built-in humidity sensor, support for "
            "multi-stage equipment and heat pumps with auxiliary heat, and a rechargeable "
            "battery that keeps it running during short power interruptions."
        ),
        p(
            "The T3 is sold under SKU LT-T3-01 at a list price of $229.00. New T3 "
            "customers receive a 30-day free trial of the Lumora Plus subscription. "
            "Several specifications differ from the Thermostat T2, including the setpoint "
            "range, the number of supported room sensors, the meaning of some error codes "
            "and the warranty term."
        ),
        h2("1.1 What Is in the Box"),
        bullets(
            "Thermostat T3 display unit and wall plate with built-in level",
            "Trim plate, two wall screws, two drywall anchors and wire labels",
            "One Lumora Room Sensor S1 (T3 bundle SKU LT-T3-02 only)",
            "Quick Start card with pairing code",
        ),
        h2("1.2 System Compatibility"),
        p(
            "The T3 supports 24 VAC conventional systems with up to 3 heat and 2 cool "
            "stages, and heat pumps with up to 2 compressor stages plus auxiliary and "
            "emergency heat. Dual-fuel systems are supported from firmware 2.3. Like the "
            "T2, the T3 is not compatible with line-voltage (120 V or 240 V) heaters."
        ),
        h1("2. Specifications"),
        table(
            ("Item", "Thermostat T3 (LT-T3)"),
            [
                ("Display", "3.5 in color capacitive touchscreen with proximity wake"),
                ("Setpoint range", "40 °F to 92 °F (4.5 °C to 33 °C)"),
                ("Temperature accuracy", "±0.5 °F (±0.3 °C)"),
                ("Humidity sensing", "0-100% RH, accuracy ±3% RH"),
                (
                    "Supported stages",
                    "Up to 3 heat / 2 cool (conventional); heat pump up to 2 compressor "
                    "stages with auxiliary and emergency heat",
                ),
                ("Power", "24 VAC, 50/60 Hz; C-wire recommended (see 3.3)"),
                ("Battery", "Rechargeable Li-ion, approx. 6 hours of operation without power"),
                ("Wireless", "802.11 a/b/g/n/ac, 2.4 GHz and 5 GHz; LumoraLink radio"),
                ("Room Sensor S1 support", "Up to 6 sensors"),
                ("Compressor protection", "5-minute minimum off-time, adjustable 2-10 minutes"),
                ("Dimensions", "4.3 x 4.3 x 0.9 in (109 x 109 x 23 mm)"),
                ("Operating environment", "32 °F to 104 °F, 5% to 90% RH non-condensing"),
                ("Warranty", "3 years (36 months) limited warranty"),
            ],
            widths=(1.2, 2.8),
            caption="Table 2-1. Thermostat T3 technical specifications.",
        ),
        note(
            "Customers frequently compare the T2 and T3. The key differences are the "
            "setpoint range (T2: 45-90 °F, T3: 40-92 °F), room sensor support (T2: 2, "
            "T3: 6), C-wire requirement (T2: required, T3: recommended) and warranty "
            "(T2: 2 years, T3: 3 years).",
            label="Comparison",
        ),
        page_break(),
        h1("3. Installation"),
        p(
            "Installation takes 30 to 60 minutes. Homes with heat pumps or more than two "
            "stages should be referred to a Lumora Certified Installer; professional "
            "installation costs a flat $129 and can extend the warranty (see the Lumora "
            "Limited Warranty Policy, LHS-POL-001)."
        ),
        h2("3.1 Before You Start"),
        steps(*_SAFETY_STEPS),
        h2("3.2 Wiring Terminals"),
        table(
            ("Terminal", "Function"),
            [
                ("R / Rc", "24 VAC power; the T3 detects a jumper automatically"),
                ("C", "24 VAC common (recommended; required in the cases listed in 3.3)"),
                ("W1 / W2 / W3", "Conventional heat stages 1-3"),
                ("Y1 / Y2", "Cool or compressor stages 1-2"),
                ("G", "Fan"),
                ("O/B", "Heat pump reversing valve"),
                ("AUX / E", "Auxiliary heat / emergency heat"),
                ("ACC+ / ACC-", "Accessory: humidifier or dehumidifier dry contacts"),
            ],
            widths=(1.0, 3.0),
            caption="Table 3-1. T3 wall plate terminals.",
        ),
        p(
            "The T3 wall plate accepts solid or stranded wire from 18 to 22 AWG. If the "
            "home has an unused wire in the bundle, installers should connect it as the "
            "C-wire at both the wall plate and the equipment control board rather than "
            "installing a PEK-1. Always confirm with a voltmeter that R to C measures "
            "between 20 and 30 VAC before attaching the display."
        ),
        h2("3.3 Homes Without a C-Wire"),
        p(
            "Unlike the T2, the T3 can usually be installed without a C-wire. It charges "
            "its internal battery from the heating and cooling circuits while the "
            "equipment is idle, and runs on the battery for up to about 6 hours during "
            "power interruptions. The battery-only mode is designed for single-stage "
            "conventional systems and has been validated on furnaces and boilers."
        ),
        p(
            "However, a C-wire or the Power Extender Kit PEK-1 is **mandatory** in three "
            "cases: heat pump systems that use auxiliary or emergency heat, any system "
            "with more than one cooling stage, and homes where the T3 controls a "
            "humidifier or dehumidifier through the ACC terminals. In these cases the T3 "
            "displays error E10 within 24 hours if no C-wire is detected, and Customer "
            "Care must arrange a PEK-1 before the case can be closed."
        ),
        h2("3.4 Mounting"),
        steps(
            "Mount the wall plate 52 to 60 in (1.3 to 1.5 m) above the floor on an "
            "interior wall, away from supply vents, windows and direct sunlight.",
            "Insert the labelled wires into the matching terminals and push the excess "
            "back into the wall.",
            "Attach the display. The T3 starts on battery immediately and asks for the "
            "equipment configuration.",
            "Restore power at the breaker and complete the setup wizard.",
        ),
        h1("4. Configuration"),
        h2("4.1 Equipment Setup"),
        p(
            "The setup wizard detects connected terminals and proposes an equipment "
            "configuration. Installers must confirm the heat pump changeover setting (O or "
            "B), the auxiliary heat lockout temperature (default 35 °F outdoor) and the "
            "number of stages before finishing."
        ),
        h2("4.2 Humidity Control"),
        p(
            "With a humidifier or dehumidifier connected to the ACC terminals, the T3 can "
            "hold indoor humidity between 30% and 60% RH. Without accessory equipment, "
            "the T3 can still dehumidify by overcooling: it runs the air conditioner up to "
            "3 °F below the cooling setpoint while humidity is above target."
        ),
        h2("4.3 Room Sensors and Occupancy"),
        p(
            "The T3 supports up to six Lumora Room Sensor S1 units. Each schedule period "
            "can use a different set of sensors, and the Follow Me mode averages only "
            "rooms where occupancy was detected in the last 30 minutes."
        ),
        page_break(),
        h1("5. Troubleshooting"),
        p(
            "Check the firmware version under Settings > About before troubleshooting. "
            "The current T3 release is 2.6.1. Battery status is shown under Settings > "
            "Power; a battery below 20% while the system is idle usually means the "
            "battery cannot charge without a C-wire."
        ),
        table(
            ("Symptom", "Likely cause", "Resolution"),
            [
                (
                    "Thermostat restarts every few hours",
                    "Battery not charging (no C-wire, multi-stage system)",
                    "Install C-wire or PEK-1; see section 3.3.",
                ),
                (
                    "Humidity reading stuck at 0% or 100%",
                    "Humidity sensing element failure",
                    "Power-cycle; if it persists the code E4 is shown - start a warranty claim.",
                ),
                (
                    "Auxiliary heat runs too often",
                    "Aux lockout set too high or droop too small",
                    "Lower aux lockout; set aux droop to 2 °F or more.",
                ),
                (
                    "Touchscreen does not respond",
                    "Screen frozen during update",
                    "Hold the screen for 10 seconds to force a restart.",
                ),
                (
                    "Sensor rooms ignored",
                    "Sensor not assigned to the current schedule period",
                    "Assign sensors in the app under Comfort > Sensors.",
                ),
            ],
            widths=(1.2, 1.5, 2.0),
            caption="Table 5-1. Common T3 symptoms.",
        ),
        h2("5.1 Factory Reset"),
        p(
            "On the T3, open Settings > Reset > Factory Reset and confirm with the 4-digit "
            "code shown on screen. If the touchscreen is unusable, remove the display "
            "from the wall plate, then press the recessed reset button on the back for 10 "
            "seconds while reattaching it."
        ),
        h1("6. Error Codes"),
        p(
            "T3 error codes share some numbers with the T2 but not their meanings. In "
            "particular, network problems are reported as E12 on the T3, while E4 on the "
            "T3 refers to the humidity sensor."
        ),
        table(
            ("Code", "Meaning", "Recommended action"),
            [
                ("E1", "Internal temperature sensor failure", "Warranty claim."),
                ("E2", "No heat detected after 20 minutes", "Check W1 and the furnace."),
                ("E3", "No cooling detected after 20 minutes", "Check Y1 and the outdoor unit."),
                ("E4", "Humidity sensor fault", "Power-cycle; warranty claim if persistent."),
                ("E5", "Room sensor not reporting for 2 hours", "Replace S1 battery."),
                (
                    "E6",
                    "Auxiliary heat running during lockout",
                    "Check AUX wiring and the outdoor temperature source.",
                ),
                ("E7", "Battery critically low", "Check C-wire; charge on USB-C if removed."),
                (
                    "E10",
                    "No C-wire detected on a configuration that requires one",
                    "Install C-wire or PEK-1 (section 3.3).",
                ),
                ("E11", "Accessory (ACC) relay fault", "Check humidifier wiring."),
                (
                    "E12",
                    "Lost connection to the wireless network for more than 10 minutes",
                    "Reconnect in Settings > Network.",
                ),
                ("E13", "Firmware update failed", "Retry after 1 hour."),
            ],
            widths=(0.5, 2.0, 2.0),
            caption="Table 6-1. Thermostat T3 error codes.",
        ),
        page_break(),
        h1("7. Warranty and Support"),
        h2("7.1 Warranty Summary"),
        p(
            "**The Thermostat T3 carries a 3-year (36-month) limited warranty from the "
            "date of delivery**, one year longer than the T2. The warranty can be extended "
            "when the T3 is professionally installed; the conditions are defined only in "
            "the Lumora Limited Warranty Policy (LHS-POL-001). Advance replacement is "
            "available for the T3 to all customers (see the Warranty Claims SOP)."
        ),
        h2("7.2 Escalation Triggers"),
        bullets(
            "Burning smell, scorch marks or a swollen battery: safety case, P1 in the "
            "Ticket Escalation SOP. Instruct the customer to remove the display from the "
            "wall and keep it away from flammable material.",
            "E1 or E4 that persists after a power-cycle: warranty claim.",
            "E10 after a PEK-1 has been installed: Tier 2 Technical Support.",
        ),
        h1("8. Appendix A: Heat Pump Configuration Reference"),
        p(
            "Use this table when helping an installer or customer configure a heat pump. "
            "Settings are under Settings > Equipment > Heat Pump. Values outside the "
            "allowed range are rejected by the setup wizard."
        ),
        table(
            ("Setting", "Default", "Allowed range", "Guidance"),
            [
                (
                    "Reversing valve",
                    "O (energize in cool)",
                    "O or B",
                    "Most systems use O; B is common on older systems from some manufacturers.",
                ),
                (
                    "Auxiliary heat lockout",
                    "35 °F outdoor",
                    "0 °F to 50 °F",
                    "Raise in cold climates if the heat pump cannot keep up.",
                ),
                (
                    "Compressor lockout",
                    "Off",
                    "-10 °F to 40 °F",
                    "Used for dual-fuel systems only.",
                ),
                (
                    "Aux heat droop",
                    "2 °F",
                    "1 °F to 5 °F",
                    "Temperature drop below setpoint before aux heat starts.",
                ),
                ("Defrost aux heat", "On", "On / Off", "Prevents cold air during defrost cycles."),
                (
                    "Emergency heat timeout",
                    "None",
                    "None, 2, 4, 8 h",
                    "Returns to normal heat after the timeout.",
                ),
            ],
            widths=(1.2, 1.0, 1.0, 2.2),
            caption="Table 8-1. T3 heat pump settings.",
        ),
        h1("9. Appendix B: Accessories and Quick Answers"),
        h2("9.1 Compatible Accessories"),
        bullets(
            "Lumora Room Sensor S1 (up to six per T3)",
            "Lumora Hub H1 (required for homes with more than one thermostat)",
            "Power Extender Kit PEK-1 (for the mandatory C-wire cases in section 3.3)",
            "T3 trim plate in white or graphite (sold separately, $12)",
        ),
        h2("9.2 Quick Answers"),
        h3("Can the T3 show outdoor temperature?"),
        p(
            "Yes. The T3 shows outdoor temperature and humidity from a weather service based "
            "on the home address. An outdoor sensor is not required."
        ),
        h3("Does the T3 work during a power outage?"),
        p(
            "The display and network connection stay on battery for about 6 hours, so the "
            "app continues to show indoor conditions. The heating and cooling equipment "
            "does not run without power."
        ),
        h3("Can the T3 screen be locked?"),
        p(
            "Yes. Settings > Lock sets a 4-digit PIN. A locked T3 still allows temperature "
            "changes within a range set by the home Owner, by default ±2 °F of the "
            "scheduled setpoint."
        ),
        h1("Revision History"),
        table(
            ("Revision", "Date", "Change"),
            [
                ("2.2", "April 20, 2026", "Clarified mandatory C-wire cases; firmware 2.6.1."),
                ("2.1", "December 1, 2025", "Added E13 and dual-fuel support."),
                ("2.0", "August 18, 2025", "Initial release for T3 hardware revision B."),
            ],
            widths=(0.8, 1.2, 3.0),
        ),
    ),
    facts=(
        fact(
            "PG-T3-01",
            "The Thermostat T3 setpoint range is 40 °F to 92 °F (4.5 °C to 33 °C).",
            "40 °F to 92 °F (4.5 °C to 33 °C)",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-02",
            "The T3 supports up to 6 Lumora Room Sensor S1 units.",
            "Up to 6 sensors",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-03",
            "On the T3, error E4 means a humidity sensor fault (network problems are E12).",
            "Humidity sensor fault",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-04",
            "On the T3, error E12 means the thermostat lost its wireless network connection "
            "for more than 10 minutes.",
            "Lost connection to the wireless network for more than 10 minutes",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-05",
            "The T3 can usually run without a C-wire, but a C-wire or PEK-1 is mandatory "
            "for heat pumps using auxiliary/emergency heat, systems with more than one "
            "cooling stage, and homes using the ACC humidifier/dehumidifier terminals; "
            "otherwise the T3 shows E10 within 24 hours.",
            "Unlike the T2, the T3 can usually be installed without a C-wire",
            "displays error E10 within 24 hours",
            kind="cross-page",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-06",
            "The Thermostat T3 has a 3-year (36-month) limited warranty from the date of delivery.",
            "3-year (36-month) limited warranty from the date of delivery",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-07",
            "The T3 compressor minimum off-time defaults to 5 minutes and is adjustable "
            "from 2 to 10 minutes.",
            "5-minute minimum off-time, adjustable 2-10 minutes",
            kind="table",
            tags=("confusable",),
        ),
        fact(
            "PG-T3-08",
            "Without accessory equipment, the T3 dehumidifies by overcooling up to 3 °F "
            "below the cooling setpoint.",
            "up to 3 °F below the cooling setpoint",
        ),
        fact(
            "PG-T3-09",
            "The T3 battery provides approximately 6 hours of operation without power.",
            "approx. 6 hours of operation without power",
            kind="table",
        ),
        fact(
            "PG-T3-10",
            "The default T3 auxiliary heat lockout temperature is 35 °F outdoor.",
            "default 35 °F outdoor",
        ),
    ),
)

# --------------------------------------------------------------------------- S1

ROOM_SENSOR_S1 = SampleDoc(
    filename="Product Guide - Lumora Room Sensor S1.pdf",
    title="Lumora Room Sensor S1 Product Guide",
    doc_type="product_guide",
    doc_number="LHS-PG-S1-001",
    revision="1.4",
    effective_date="January 12, 2026",
    owner="Product Support Engineering",
    audience="Customer Care, Technical Support",
    purpose=(
        "Reference for supporting the Lumora Room Sensor S1 (model LS-S1), a battery "
        "powered temperature and occupancy sensor used with the Thermostat T2, "
        "Thermostat T3 and Hub H1."
    ),
    blocks=(
        h1("1. Product Overview"),
        p(
            "The Room Sensor S1 measures temperature and detects occupancy in the room "
            "where it is placed. Thermostats use these readings to balance comfort "
            "between rooms. The S1 communicates over the LumoraLink low-power radio and "
            "does not connect to the home wireless network directly."
        ),
        p(
            "The S1 is sold as a single unit (SKU LS-S1-01, $39.00) and as a two-pack "
            "(SKU LS-S1-02, $69.00). It can be paired with a Thermostat T2 (maximum 2 "
            "sensors), a Thermostat T3 (maximum 6 sensors) or a Hub H1, which allows the "
            "sensor to be used for automations without a thermostat."
        ),
        h1("2. Specifications"),
        table(
            ("Item", "Room Sensor S1 (LS-S1)"),
            [
                ("Sensors", "Temperature, passive infrared (PIR) occupancy"),
                ("Temperature accuracy", "±0.9 °F (±0.5 °C)"),
                ("Occupancy detection", "Up to 15 ft (4.5 m), 100° horizontal field of view"),
                ("Radio", "LumoraLink 915 MHz"),
                ("Range", "Up to 60 ft (18 m) indoors to the thermostat or hub"),
                ("Battery", "One CR2477 3 V lithium coin cell (included)"),
                ("Battery life", "Up to 2 years at the default 5-minute reporting interval"),
                ("Low battery warning", "Sent to the app at 15% remaining"),
                ("Operating environment", "32 °F to 104 °F, indoor use only"),
                ("Dimensions", "1.8 x 1.8 x 0.6 in (46 x 46 x 15 mm)"),
                ("Warranty", "1 year (12 months) limited warranty"),
            ],
            widths=(1.2, 2.8),
            caption="Table 2-1. Room Sensor S1 specifications.",
        ),
        p(
            "Setting the reporting interval to 1 minute in the app (Sensors > Advanced) "
            "improves responsiveness but reduces battery life to about 8 months. The "
            "interval cannot be set longer than 10 minutes."
        ),
        h1("3. Placement and Pairing"),
        h2("3.1 Placement Guidelines"),
        bullets(
            "Place the sensor about 5 ft (1.5 m) above the floor on an interior wall or shelf.",
            "Keep it at least 3 ft away from windows, exterior doors, supply vents, "
            "fireplaces and electronics that produce heat.",
            "For occupancy detection, point the lens toward the main seating or sleeping "
            "area. The sensor does not detect motion through glass.",
            "Do not install the S1 in bathrooms, garages, attics or outdoors.",
        ),
        h2("3.2 Pairing Procedure"),
        steps(
            "In the Lumora Home app, open the thermostat or hub and tap Add Sensor.",
            "Pull the battery tab out of the sensor. The LED blinks blue to show it is in "
            "pairing mode for 3 minutes.",
            "Hold the sensor within 30 ft (9 m) of the thermostat or hub during pairing; "
            "it can be moved to its final location afterwards.",
            "Wait for three green blinks, then name the room in the app.",
            "To re-enter pairing mode later, press and hold the button on the back for 5 "
            "seconds until the LED blinks blue.",
        ),
        page_break(),
        h1("4. LED Indicators"),
        table(
            ("LED pattern", "Meaning", "Action"),
            [
                ("Blinking blue", "Pairing mode (3 minutes)", "Complete pairing in the app."),
                ("Three green blinks", "Paired successfully", "None."),
                (
                    "Single green blink",
                    "Occupancy detected (first 30 minutes after pairing only)",
                    "None; used for placement testing.",
                ),
                ("Red double blink", "Pairing failed", "Move closer and retry pairing."),
                ("Slow amber blink every 60 s", "Battery below 15%", "Replace the CR2477 battery."),
                (
                    "Solid red for 5 s",
                    "Hardware fault",
                    "Remove battery for 30 s; if repeated, warranty claim.",
                ),
            ],
            widths=(1.3, 1.7, 1.6),
            caption="Table 4-1. S1 LED patterns.",
        ),
        h1("5. Troubleshooting"),
        h2("5.1 Sensor Shows Offline"),
        steps(
            "Check the battery level in the app. Replace the battery if it is below 15% or "
            "if the sensor has been offline for more than 2 hours (thermostats report "
            "error E5).",
            "Confirm the sensor is within 60 ft of the thermostat or hub. Metal "
            "appliances, mirrors and concrete walls reduce range significantly.",
            "Press the button once. If the LED does not light at all, the battery is "
            "fully discharged or inserted upside down (the + side faces the cover).",
            "Remove the sensor from the app and pair it again.",
        ),
        h2("5.2 Temperature Differs From the Thermostat"),
        p(
            "Differences of up to 2 °F between rooms are normal. If a sensor reads more "
            "than 2 °F differently from a reference thermometer placed beside it for 30 "
            "minutes, apply an offset in the app (up to ±5 °F). A difference above 5 °F "
            "after an offset indicates a faulty sensor and qualifies for a warranty "
            "claim."
        ),
        h2("5.3 Occupancy Not Detected"),
        p(
            "PIR sensors detect movement of warm bodies. A person sitting still may not "
            "be detected for several minutes. The thermostat keeps a room marked as "
            "occupied for 30 minutes after the last detection. Pets under 40 lb are "
            "usually ignored when the sensor is mounted at 5 ft."
        ),
        h1("6. Battery Replacement"),
        steps(
            "Twist the back cover counter-clockwise and lift it off.",
            "Replace the CR2477 cell with the + side facing the cover. A CR2032 will not "
            "fit and must not be used.",
            "Close the cover. The sensor reconnects automatically within 2 minutes; no "
            "re-pairing is needed.",
        ),
        note(
            "Batteries are consumables and are not covered by the S1 warranty. Customer "
            "Care may send one free replacement battery per sensor during the first year "
            "as a goodwill gesture.",
        ),
        h1("7. Comfort Strategies With Several Sensors"),
        p(
            "Customers often ask how the thermostat uses several sensors. Agents can "
            "explain the three comfort modes available in the app under Comfort > Sensors:"
        ),
        table(
            ("Mode", "How it works", "Best for"),
            [
                (
                    "Average",
                    "Averages the thermostat and all selected sensors equally",
                    "Open-plan homes with small differences between rooms",
                ),
                (
                    "Priority room",
                    "Uses only one selected room for the current schedule period",
                    "Bedrooms at night, home office during the day",
                ),
                (
                    "Follow Me (T3 only)",
                    "Averages only rooms with occupancy in the last 30 minutes",
                    "Homes where people move between rooms",
                ),
            ],
            widths=(1.1, 2.2, 1.8),
            caption="Table 7-1. Sensor comfort modes.",
        ),
        p(
            "The T2 supports the Average and Priority room modes only. With either "
            "thermostat, a sensor that has not reported for 2 hours is removed from the "
            "calculation until it reports again."
        ),
        h1("8. Quick Answers for Agents"),
        h3("Can the S1 be used outdoors or in a garage?"),
        p(
            "No. The S1 is rated for indoor use from 32 °F to 104 °F. Readings outside "
            "this range are not reliable and condensation can damage the sensor."
        ),
        h3("Does the S1 measure humidity?"),
        p(
            "No. The S1 measures temperature and occupancy only. Humidity is measured by "
            "the Thermostat T3."
        ),
        h3("Can one sensor be shared by two thermostats?"),
        p(
            "No. Each sensor is paired with exactly one thermostat or hub. In homes with "
            "two zones, pair each sensor with the thermostat of the zone where it is "
            "installed."
        ),
        h3("Is the S1 a camera or microphone?"),
        p(
            "No. The PIR sensor only detects changes in infrared heat. It cannot record "
            "images or sound."
        ),
        h1("9. Appendix: Placement Examples by Room"),
        table(
            ("Room", "Recommended placement", "Avoid"),
            [
                (
                    "Bedroom",
                    "Dresser or wall facing the bed, 4-5 ft high",
                    "Nightstand next to a lamp or phone charger",
                ),
                (
                    "Living room",
                    "Bookshelf facing the seating area",
                    "Above a TV or near a fireplace",
                ),
                ("Home office", "Wall facing the desk", "On the desk next to a computer"),
                (
                    "Nursery",
                    "Wall away from the crib, out of reach",
                    "Inside the crib or on the floor",
                ),
                ("Kitchen", "Not recommended", "Cooking heat causes false readings"),
                (
                    "Basement living area",
                    "Interior wall away from the furnace",
                    "Near the furnace, water heater or sump pump",
                ),
            ],
            widths=(1.1, 2.0, 2.0),
            caption="Table 9-1. Placement examples.",
        ),
        p(
            "The S1 is small enough to swallow and the coin cell is hazardous if swallowed. "
            "In nurseries and children's rooms, always mount the sensor out of reach using "
            "the included adhesive pad or screw mount, and confirm the back cover is "
            "fully closed."
        ),
        h1("10. Warranty"),
        p(
            "**The Room Sensor S1 carries a 1-year (12-month) limited warranty.** Sensors "
            "are not eligible for advance replacement unless the customer has an active "
            "Lumora Plus subscription. See the Lumora Limited Warranty Policy "
            "(LHS-POL-001) for full terms."
        ),
    ),
    facts=(
        fact(
            "PG-S1-01",
            "The Room Sensor S1 battery (one CR2477 coin cell) lasts up to 2 years at the "
            "default 5-minute reporting interval.",
            "Up to 2 years at the default 5-minute reporting interval",
            kind="table",
        ),
        fact(
            "PG-S1-02",
            "The S1 range is up to 60 ft (18 m) indoors to the thermostat or hub.",
            "Up to 60 ft (18 m) indoors",
            kind="table",
        ),
        fact(
            "PG-S1-03",
            "During pairing, the S1 must be held within 30 ft (9 m) of the thermostat or hub.",
            "within 30 ft (9 m) of the thermostat or hub",
        ),
        fact(
            "PG-S1-04",
            "An S1 slow amber blink every 60 seconds means the battery is below 15%.",
            "Slow amber blink every 60 s",
            kind="table",
        ),
        fact(
            "PG-S1-05",
            "Setting the S1 reporting interval to 1 minute reduces battery life to about 8 months.",
            "reduces battery life to about 8 months",
        ),
        fact(
            "PG-S1-06",
            "An S1 reading more than 5 °F off after an offset is applied indicates a faulty "
            "sensor and qualifies for a warranty claim.",
            "A difference above 5 °F after an offset indicates a faulty sensor",
        ),
        fact(
            "PG-S1-07",
            "The Room Sensor S1 has a 1-year (12-month) limited warranty and is not "
            "eligible for advance replacement unless the customer has Lumora Plus.",
            "The Room Sensor S1 carries a 1-year (12-month) limited warranty.",
        ),
    ),
)

# --------------------------------------------------------------------------- H1

HUB_H1 = SampleDoc(
    filename="Product Guide - Lumora Hub H1.pdf",
    title="Lumora Hub H1 Product Guide",
    doc_type="product_guide",
    doc_number="LHS-PG-H1-001",
    revision="1.7",
    effective_date="February 9, 2026",
    owner="Product Support Engineering",
    audience="Customer Care, Technical Support",
    purpose=(
        "Reference for supporting the Lumora Hub H1 (model LH-H1), the bridge that "
        "connects LumoraLink sensors and thermostats to the home network and runs local "
        "automations."
    ),
    blocks=(
        h1("1. Product Overview"),
        p(
            "The Hub H1 bridges LumoraLink devices to the internet and to the Lumora Home "
            "app. It stores schedules and automations locally so that the home keeps "
            "working when the internet connection is down. A hub is optional for homes "
            "with a single thermostat but required for sensor-only setups and for homes "
            "with more than one thermostat."
        ),
        p(
            "The H1 is sold under SKU LH-H1-01 at a list price of $79.00. It connects up "
            "to 32 LumoraLink devices, including thermostats, room sensors and future "
            'accessories. Devices beyond 32 are rejected with the message "Hub is '
            'full"; a second hub can be added to the same home.'
        ),
        h1("2. Specifications"),
        table(
            ("Item", "Hub H1 (LH-H1)"),
            [
                ("Radios", "LumoraLink 915 MHz mesh; 802.11 b/g/n 2.4 GHz"),
                ("Wired network", "One 10/100 Ethernet port (cable included)"),
                ("Device capacity", "Up to 32 LumoraLink devices"),
                ("Power", "5 V 2 A USB-C adapter (included); no battery"),
                ("Local storage", "Schedules and automations for up to 7 days offline"),
                ("Firmware updates", "Automatic, between 2:00 and 4:00 AM local time"),
                ("Dimensions", "3.5 x 3.5 x 1.0 in (89 x 89 x 25 mm)"),
                ("Warranty", "2 years (24 months) limited warranty"),
            ],
            widths=(1.2, 2.8),
            caption="Table 2-1. Hub H1 specifications.",
        ),
        h1("3. Installation"),
        steps(
            "Place the hub in a central location, at least 3 ft from the router and away "
            "from large metal objects. A shelf at mid-height gives the best mesh range.",
            "Connect the USB-C power adapter. Use the included adapter; low-power phone "
            "chargers cause random restarts.",
            "Optionally connect the Ethernet cable to the router. Ethernet is recommended "
            "when more than 15 devices are paired.",
            "In the Lumora Home app tap Add Device > Hub and scan the QR code on the "
            "bottom of the hub.",
            "Wait until the status light turns solid teal. Setup normally takes 2 to 5 "
            "minutes, longer if a firmware update is installed during setup.",
        ),
        h2("3.1 Placement Guidance"),
        table(
            ("Location", "Suitability", "Comment"),
            [
                ("Central hallway shelf", "Best", "Good mesh coverage for most homes."),
                (
                    "Next to the router",
                    "Acceptable",
                    "Keep at least 3 ft apart to avoid interference.",
                ),
                (
                    "Inside a metal cabinet or media rack",
                    "Avoid",
                    "Metal blocks the LumoraLink radio.",
                ),
                ("Basement", "Avoid", "Sensors on upper floors may lose connection."),
                (
                    "Garage or outdoors",
                    "Not supported",
                    "Operating range 32 °F to 104 °F, indoor use only.",
                ),
            ],
            widths=(1.6, 1.0, 2.4),
            caption="Table 3-1. Hub placement.",
        ),
        page_break(),
        h1("4. Status Light"),
        table(
            ("Light", "Meaning", "Action"),
            [
                ("Solid teal", "Online and working normally", "None."),
                (
                    "Pulsing amber",
                    "Setting up or installing an update",
                    "Wait up to 15 minutes; do not unplug.",
                ),
                ("Blinking amber", "Factory reset in progress", "Wait for restart."),
                (
                    "Blinking red",
                    "No internet connection; local control still works",
                    "Check router; reconnect in the app.",
                ),
                (
                    "Solid red",
                    "Hardware fault",
                    "Unplug for 1 minute; if it returns, start an RMA.",
                ),
                ("Off", "No power", "Check the adapter and outlet."),
            ],
            widths=(1.0, 2.0, 1.7),
            caption="Table 4-1. H1 status light.",
        ),
        h1("5. Offline Operation"),
        p(
            "If the internet connection is lost, the H1 keeps running schedules and "
            "automations stored on the device for up to 7 days. After 7 days without a "
            "connection, time-based automations pause until the clock can be verified, "
            "but thermostats continue their own schedules. Remote access from the app is "
            "not available while the hub is offline, but the app can still control "
            "devices when the phone is on the same local network."
        ),
        h1("6. Troubleshooting"),
        h2("6.1 Devices Drop Off the Hub"),
        bullets(
            "Check how many devices are paired; the limit is 32.",
            "Move the hub away from the router, microwave ovens and cordless phone bases.",
            "Add a mains-powered LumoraLink device (such as a thermostat) between the hub "
            "and distant sensors to extend the mesh.",
        ),
        h2("6.2 Factory Reset"),
        p(
            "To factory reset the H1, press and hold the reset button on the bottom with a "
            "paper clip for 15 seconds until the status light blinks amber. All paired "
            "devices must be paired again afterwards. Before suggesting a reset, confirm "
            "the customer can access the app to re-add devices."
        ),
        h2("6.3 Firmware"),
        p(
            "The current H1 firmware is 5.2.0. Updates install automatically between 2:00 "
            "and 4:00 AM local time. Customers cannot postpone updates for more than 14 "
            "days; after 14 days the update installs at the next maintenance window."
        ),
        page_break(),
        h1("7. Network Requirements"),
        table(
            ("Requirement", "Value"),
            [
                ("Wireless band", "2.4 GHz (5 GHz-only networks are not supported)"),
                (
                    "Security",
                    "Password-protected personal network; enterprise sign-in is not supported",
                ),
                ("Outbound ports", "TCP 443 and 8883 must be open"),
                ("Bandwidth", "Less than 50 MB per month for a typical home"),
                ("Captive portals", "Not supported (hotel, dormitory or guest networks)"),
                ("IP addressing", "DHCP required; a reserved address is recommended"),
            ],
            widths=(1.4, 3.4),
            caption="Table 7-1. Hub H1 network requirements.",
        ),
        p(
            "If the customer's router uses a firewall with strict outbound rules, ask the "
            "customer or their network administrator to allow TCP ports 443 and 8883. A "
            "blinking red light together with a working internet connection for other "
            "devices usually points to blocked ports."
        ),
        h1("8. Homes With More Than One Hub"),
        p(
            "Large homes or homes with more than 32 devices can use additional hubs. Each "
            "device is paired to exactly one hub. Automations can use devices from any hub "
            "in the same home, but they run in the cloud rather than locally when they "
            "combine devices from different hubs, so they stop during an internet outage."
        ),
        steps(
            "Add the second hub in the app under Add Device > Hub.",
            "Choose which existing devices to move. The app moves them one at a time; each "
            "move takes about 30 seconds.",
            "Check the mesh map in Settings > Network > Mesh to confirm every device has a "
            "strong or good signal.",
        ),
        h1("9. Automations"),
        p(
            "The H1 runs automations that combine triggers and actions, for example "
            '"when nobody is home after 9:00 AM, set the thermostat to Away". Each home can '
            "have up to 50 automations. Automations that use only devices on one hub run "
            "locally on that hub."
        ),
        table(
            ("Trigger type", "Examples"),
            [
                ("Time", "Specific time, sunrise or sunset with an offset"),
                ("Occupancy", "Room occupied or empty for a set time (from S1 sensors)"),
                ("Temperature", "A room is above or below a threshold"),
                ("Presence", "First member arrives or last member leaves (Away mode)"),
            ],
            widths=(1.2, 3.6),
            caption="Table 9-1. Automation triggers.",
        ),
        h1("10. Quick Answers for Agents"),
        h3("Does a home with one thermostat need a hub?"),
        p(
            "No. A single T2 or T3 connects directly to the home network. A hub is needed "
            "for homes with more than one thermostat, for sensor-only setups and for local "
            "automations."
        ),
        h3("Can the H1 run on battery during a power outage?"),
        p(
            "No. The H1 has no battery. Customers who want the hub to stay online during "
            "outages can connect it and the router to a small uninterruptible power supply."
        ),
        h3("Can the H1 connect to the 5 GHz band?"),
        p(
            "No. The H1 wireless radio supports 2.4 GHz only. If the router offers only 5 "
            "GHz, connect the hub with the Ethernet cable instead."
        ),
        h1("11. Warranty and Replacement"),
        p(
            "**The Hub H1 carries a 2-year (24-month) limited warranty.** Advance "
            "replacement is available for the H1 to all customers because the home loses "
            "remote access while the hub is out of service. A solid red light that "
            "returns after a power-cycle is treated as a confirmed hardware fault and "
            "does not require further troubleshooting before an RMA is created."
        ),
    ),
    facts=(
        fact(
            "PG-H1-01",
            "The Hub H1 connects up to 32 LumoraLink devices; additional devices are "
            'rejected with "Hub is full".',
            "Up to 32 LumoraLink devices",
            kind="table",
        ),
        fact(
            "PG-H1-02",
            "The H1 installs firmware updates automatically between 2:00 and 4:00 AM local "
            "time, and updates cannot be postponed for more than 14 days.",
            "cannot postpone updates for more than 14 days",
        ),
        fact(
            "PG-H1-03",
            "A blinking red H1 status light means no internet connection, while local "
            "control still works.",
            "No internet connection; local control still works",
            kind="table",
        ),
        fact(
            "PG-H1-04",
            "To factory reset the H1, hold the reset button for 15 seconds until the light "
            "blinks amber; all devices must then be paired again.",
            "paper clip for 15 seconds until the status light blinks amber",
        ),
        fact(
            "PG-H1-05",
            "When offline, the H1 keeps running locally stored schedules and automations "
            "for up to 7 days.",
            "stored on the device for up to 7 days",
        ),
        fact(
            "PG-H1-06",
            "The Hub H1 has a 2-year (24-month) limited warranty and advance replacement "
            "is available to all customers.",
            "The Hub H1 carries a 2-year (24-month) limited warranty.",
        ),
        fact(
            "PG-H1-07",
            "Ethernet is recommended for the H1 when more than 15 devices are paired.",
            "Ethernet is recommended when more than 15 devices are paired",
        ),
    ),
)

PRODUCT_GUIDES = (THERMOSTAT_T2, THERMOSTAT_T3, ROOM_SENSOR_S1, HUB_H1)
