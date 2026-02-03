# Home Assistant Context & Best Practices

This document serves as a "Knowledge Base" for the AI Agent to understand the specific context of Home Assistant as of 2026, as well as project-specific architectural decisions.

## 🏠 Home Assistant Core Concepts (2026 Edition)

### 1. The "Open Home" Philosophy
*   **Privacy & Local Control**: All logic should run locally whenever possible. Cloud dependencies should be avoided unless explicitly requested (e.g., specific cloud-only integrations).
*   **Durability**: Automations should be robust and survive restart.
*   **Data Ownership**: User data belongs to the user (e.g., the new Device Database is opt-in).

### 2. Configuration Best Practices
*   **UI vs. YAML**:
    *   **Integrations**: Most modern integrations are configured via the UI (Config Flow). Do NOT suggest adding `discovery:`, `mqtt:`, or integration-specific blocks to `configuration.yaml` unless that integration explicitly *requires* YAML (e.g., `template`, `command_line`, `rest`).
    *   **Logic**: Complex logic (Templates, Automations, Scripts) is often better managed in YAML for version control and complexity management, though the UI editors are powerful.
*   **Entity Naming**:
    *   Use descriptive entity IDs: `binary_sensor.kitchen_motion` (Good) vs `binary_sensor.hue_motion_sensor_1` (Bad).
    *   Avoid changing entity IDs after creation if possible, as it breaks history.

### 3. Automation Patterns
*   **Triggers**: Use "Device" triggers for simple things, but "State" or "Event" triggers for stability and portability.
*   **Conditions**: ALWAYS use conditions to preventing "flapping" or unwanted runs (e.g., `condition: state` check `sun`).
*   **Modes**:
    *   `single`: Default. Good for most things.
    *   `restart`: vital for motion-activated lights (re-start the timer).
    *   `parallel`: Use with caution.

## 🛠️ Project Specific Context

### Agent Architecture
*   **Safety First**: We prioritize the "Safety Net". If a change *might* break boot, we must suggest a `git_commit` first.
*   **System Awareness**: Before suggesting an automation, we should verify the entities exist using `get_system_info` (future tool).

### Common Mistakes to Avoid
*   **Legacy Groups**: Do not use the old `group:` platform for lights/switches. Use the helper (UI) or the modern platform-specific group integration.
*   **Secrets**: NEVER reveal or log `secrets.yaml` content. Reference them as `!secret wifi_password`.
*   **Restarting**: Don't restart Core for a simple YAML change unless necessary. Use `reload` services (e.g., `automation.reload`) whenever possible.

---

## 🔬 Deep Research: Recent & Upcoming HA Changes

### 🚨 Critical Behavioral Guidelines (Feb 2026)
Based on recent architectural shifts (2025.11 - 2026.2), the Agent must adhere to these new standards:

1.  **Enforce Syntactic Modernization**:
    *   **Rule**: STRICTLY use `template:` top-level domain.
    *   **Prohibited**: `platform: template` (Legacy). This is a "time-bomb" deprecation (Dead by June 2026).
    *   **Action**: Flag and refactor any legacy template code immediately.

2.  **Think in Containers (Targeting)**:
    *   **Rule**: Prioritize **Areas** (`area_id`) and **Devices** over specific Entity IDs.
    *   **Why**: "Turn on Living Room Lights" (`area_id: living_room`) is robust. "Turn on light.bulb_3" is fragile.
    *   **Action**: Use the new Target Picker logic in automations.

3.  **Adopt the New Lexicon (2026.2)**:
    *   **Apps**: Supervisor add-ons are now "Apps".
    *   **Integrations**: For device connections.
    *   **Labs**: Experimental features (Opt-in).

4.  **Leverage Community Intelligence**:
    *   **Device Database**: Use the new "Open Home Device Database" (Labs) to check device reliability before recommending hardware.
    *   **Spook**: Use Spook integration diagnostics for "garbage collection" of orphaned entities.

5.  **Privacy-First Architecture**:
    *   **Rule**: Prioritize local control (Zigbee, Matter, Local LLMs).
    *   **Warning**: Warn users about cloud-polling integrations.

### 📅 Release Context
*   **2026.1**: Semantic "Purpose-Specific Triggers" (e.g., `trigger: lock.unlocked`).
*   **2026.2 (Beta)**: "Apps" rename, Device Database launch, Group Sensor strict validation.

*For full details, see: [`ha-config-ai-agent/docs/Home Assistant AI Context Research.md`](ha-config-ai-agent/docs/Home%20Assistant%20AI%20Context%20Research.md)*

