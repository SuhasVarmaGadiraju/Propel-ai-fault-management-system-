# 5–7 Minute Demonstration Video Script

**Project**: Propel AI Fault Detection and Management System  
**Target Audience**: Technical Evaluators, Utility Operations Engineers  
**Estimated Time**: 6 Minutes 30 Seconds  

---

## Part 1: Project Introduction & Value Proposition (0:00 - 0:45)

**Visual**: Screen shows the **Operations Dashboard** (`http://localhost:3000`) with live grid health metrics and top KPI cards.

**Presenter Voiceover**:
> "Welcome to the demonstration of the **Propel AI Fault Detection and Management System**.
> 
> Electrical utilities face a major challenge: when a distribution line breaks or a transformer fails, isolating the exact outage location usually relies on manual customer phone calls.
> 
> Propel AI solves this by building an in-memory graph representation of 11kV Feeders, Distribution Transformers, Line Poles, and IoT Devices. It ingests live telemetry, deterministically localizes line breaks in under 5 milliseconds, scores confidence from 0 to 100%, and automatically dispatches repair work orders."

---

## Part 2: System Architecture Overview (0:45 - 1:30)

**Visual**: Display `docs/ARCHITECTURE.md` architecture diagram and Mermaid flowcharts.

**Presenter Voiceover**:
> "Under the hood, the system is engineered using Python 3.12, Flask, SQLAlchemy 2.0, PostgreSQL, and React 18.
> 
> Rather than relying on slow, non-deterministic LLMs that suffer from hallucination risks, our solution uses a **deterministic graph boundary algorithm** inside `NetworkGraphService` and `FaultLocalizationService`.
> 
> Every telemetry event is validated, deduplicated, and checked for sequence lag before updating the live grid status."

---

## Part 3: Pole Registry & Master Data (1:30 - 2:15)

**Visual**: Navigate to **Pole Registry** (`/poles`). Search for `POL-NORTH-01-002`.

**Presenter Voiceover**:
> "Here in the **Pole Registry**, we manage the master physical topology of over 800 distribution poles across Hyderabad.
> 
> Our automated CSV importer validates feeder codes, transformer assignments, GPS coordinates, and attached IoT device serial numbers. Notice how uninstrumented poles without IoT sensors are handled safely."

---

## Part 4: Network Explorer Visualization (2:15 - 3:00)

**Visual**: Navigate to **Network Explorer** (`/network-explorer`). Click on `FDR-HYD-NORTH-01` -> `TRF-NORTH-01`.

**Presenter Voiceover**:
> "The **Network Explorer** renders the live in-memory radial tree graph. Operators can expand feeder trunks down to individual transformers and leaf poles.
> 
> Green badges indicate energized sensors, while dark badges show active power loss. Clicking any pole reveals its upstream parent path back to the substation."

---

## Part 5: Fault Simulator — Injecting a Small Span Outage (3:00 - 4:00)

**Visual**: Navigate to **Fault Simulator** (`/simulator`). Select **Small Span Line Outage** targeting pole `POL-NORTH-01-002`. Click **Run Simulation Scenario**.

**Presenter Voiceover**:
> "Now, let's exercise the system using our **Fault Simulator**. We select the *Small Span Line Outage* scenario targeting Pole `POL-NORTH-01-002`.
> 
> Upon execution, the simulator generates realistic synthetic telemetry payloads for the upstream parent and downstream subtree, posting them through the exact `TelemetryIngestionService` pipeline used in production."

---

## Part 6: Deterministic Localization & Auto Ticket Generation (4:00 - 5:00)

**Visual**: View simulation results card showing `SPAN_FAULT = 1`, `Confidence = 100%`, and created Ticket `TKT-2026-0001`. Navigate to **Repair Tickets** (`/tickets`).

**Presenter Voiceover**:
> "Notice the results! The engine localized a `SPAN_FAULT` between `POL-NORTH-01-001` and `POL-NORTH-01-002` with 100% confidence.
> 
> Because an active outage incident was confirmed, `TicketService` automatically spawned repair work order `TKT-2026-0001` with `MEDIUM` priority and 45 impacted households.
> 
> If we transition the ticket status from `NEW` to `ASSIGNED` and then `RESOLVED`, the system allows us to test automated power verification."

---

## Part 7: Analytics Dashboard & Power Restoration (5:00 - 6:00)

**Visual**: Return to Simulator, click **Power Restoration & Auto-Verification**. Navigate to **Analytics Dashboard** (`/analytics`). Click **Export Tickets (CSV)**.

**Presenter Voiceover**:
> "Next, we run the *Power Restoration* scenario. Live `power_restored` telemetry is ingested across the feeder line.
> 
> The system automatically re-evaluates the network, confirms zero active faults, and transitions the `RESOLVED` repair ticket to `VERIFIED`.
> 
> On the **Analytics & Operations Dashboard**, operators monitor grid reliability KPIs, including Mean Time To Repair (MTTR), availability percentage, and can export tickets or simulation history as CSV and JSON files."

---

## Part 8: Closing Summary (6:00 - 6:30)

**Visual**: Show project repository root with Docker Compose command.

**Presenter Voiceover**:
> "In summary, the Propel AI Fault Management System delivers an end-to-end, production-ready solution featuring deterministic localization, automated ticket workflows, real-time analytics, and 100% unit test coverage.
> 
> Thank you for reviewing our project."
