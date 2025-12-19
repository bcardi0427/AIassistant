This is the repository for the Home Assistant Configuration AI Agent add-on.

An AI-powered Home Assistant configuration assistant with approval workflow.

**Chat with your configuration:**
- "Enable debug logging for the MQTT integration"
- "Show me all my automations that involve lights"
- "Rename my 'Office Button' device to 'Desk Button'"
- "Create an automation that turns on the porch light at sunset"

# Installation

[![Open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=yinzara&repository=ha-config-ai-agent&category=Integration)
1. **Install:** 
   - Search for "AI Configuration Agent"
   - Click Download
   - Restart Home Assistant

2. **Configure:**
   - Settings → Devices & Services → Add Integration
   - Search "AI Configuration Agent"
   - Enter API key and settings

# Features
* 🤖 **Natural Language Interface** - No YAML expertise required
* ✅ **Approval Workflow** - Review visual diffs before applying changes
* 🔒 **Safe Operations** - Automatic backups, validation, and rollback
* 📊 **Visual Diffs** - See exactly what will change
* 🔌 **Flexible AI Providers** - OpenAI, OpenRouter, Ollama, Azure, or any OpenAI-compatible API
* 📝 **Configuration Management** - Automations, scripts, Lovelace, devices, entities, and areas
* 🔄 **Auto-Reload** - Home Assistant configuration reloads automatically after changes
