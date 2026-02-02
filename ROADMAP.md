# Future Feature Roadmap

This document outlines potential features for future releases of the AI Configuration Agent.

## 🧠 System Awareness & Context
The goal is to make the agent "know" your home better so it makes fewer mistakes.

- **[ ] Device & Entity Registry Access**: Allow the agent to search for "that light in the kitchen" by looking up devices and areas, not just guessing entity IDs.
- **[ ] Device Discovery & Recommendation**:
    - Scan the network for unconfigured devices.
    - **Integration with the new "Open Home Device Database"**:
        - Utilizing the new 2026.2 Device Database to match devices to high-quality integrations.
        - Helping users opt-in to the "Labs" feature to contribute analytics if they choose.
        - Using this community-driven data to recommend the *best* integration when multiple exist.
- **[ ] Blueprint-Driven Setup**:
    - **Contextual Recommendations**: "You just added a Philips Hue Dimmer Switch. Would you like to use this comprehensive Blueprint to configure it?"
    - **Smart Instantiation**: The agent can fill in the Blueprint inputs for you by finding the matching entities in your registry.
    - **Blueprint Exchange Integration**: Ability to search for and import community blueprints to solve specific device needs.
- **[ ] Log Analysis**: Automated analysis of error logs to suggest fixes for broken integrations or automations.

## 🛡️ Safety & Reliability
Enhancing the "Safety Net" features.

- **[ ] Dry-Run Automation Tracing**: Simulate automation triggers to see what *would* happen without actually running them.
- **[ ] Scheduled Backups**: Auto-commit to Git on a schedule (e.g., nightly).
- **[ ] Conflict Resolution**: Smart handling when the agent tries to edit a file you just changed manually.

## 🖥️ User Experience (UI)
Making the agent feel like a native part of Home Assistant.

- **[ ] Sidebar Integration (Native Panel)**: A proper panel in the HA sidebar (not just an iframe) with better theming.
- **[ ] Mobile-Friendly View**: Optimizing the chat interface for the HA Companion App.
- **[ ] Quick Actions**: Buttons for common requests like "Check Config", "Show Logs", "Commit Changes".

## 🔧 Advanced Configuration
Power-user tools.

- **[ ] Dashboard/Lovelace Generation**: Advanced tools to create entire dashboard views from a prompt.
- **[ ] ESPHome Support**: Ability to write and compile ESPHome YAML configs.
- **[ ] Scene Generation**: "Set the mood" by generating complex scenes based on available entities.
