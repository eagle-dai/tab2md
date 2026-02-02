# Tool: tab2md

## Description

A bridge utility that allows AI Agents to "see" what the user is currently viewing in their browser. It captures the DOM state of the active tab (bypassing auth walls) and transforms it into semantic Markdown.

## Usage

- **Command:** `uv run tab2md`
- **Context:** Requires a local Chromium browser running on port 9222.
- **Output:** Returns a local file path to the generated Markdown.

## Best Practices

- Use this when the user asks to "summarize this page" or "extract code from this tab".
- It handles dynamic JS content (SPA) and authenticated sessions automatically.
