# Deep Research Prompt for Home Assistant Context

**Instructions**: Copy and paste the prompt below into a "Reasoning Application" or a model with web access (like Gemini Advanced or ChatGPT o1/Pro). Then paste the result into `HA_CONTEXT.md`.

---

**Prompt:**

> I am building a "Context File" for an AI Coding Agent that manages a Home Assistant instance. I need you to perform a deep research dive into the state of Home Assistant as of **February 2026** (covering the last 4 months).
>
> Please research and summarize the following four areas. For each point, you **MUST** include an "Impact on AI" note explaining how the Agent should change its behavior (e.g., "Stop acting like X, start acting like Y").
>
> **1. Core Updates (Last 3 Major Versions)**
> *   What are the headline features for 2025.11, 2025.12, 2026.1, and the 2026.2 Beta?
> *   Are there any **Breaking Changes** or **Deprecations** (especially in YAML configuration)?
> *   *Goal: Ensure the Agent doesn't write deprecated YAML or obsolete template code.*
>
> **2. The "Labs" & Beta Features**
> *   What is currently in Home Assistant "Labs"? (e.g., The "Open Home Device Database").
> *   How does it work, and should the User opt-in?
> *   *Goal: Enable the Agent to suggest enabling these bleeding-edge features during setup.*
>
> **3. HACS & Community Trends**
> *   What are the trending/popular new custom integrations or frontend cards in HACS recently?
> *   Are there any "Must Have" replacements for standard integrations? (e.g., "Use X custom component instead of the built-in Y because it's broken").
>
> **4. Future Roadmap**
> *   What are the announced focus areas for 2026? (e.g., "Year of the Open Home", "Voice Chapter 3", etc.).
> *   What hardware or protocols are getting special attention? (e.g., Thread, Matter, Voice Satellite hardware).
>
> **Output Format:**
> Please structure the output as Markdown, ready to be pasted into a file named `HA_CONTEXT.md`. Use the following structure for each item:
> - **[Feature/Change Name]**
>   - *Summary*: 1-sentence description.
>   - *Behavior Change*: "The Agent should now..."
>   - *Code Example* (if applicable): Show the NEW way to do it.
