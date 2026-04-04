# Plan: Add Dark Mode Support
## Goal
Implement a dark mode toggle that persists user preference across sessions.
## Background
The app currently uses a hard-coded light theme. Users have requested dark mode support.
## Steps
### 1. Add CSS variables for theme tokens
Define `--color-bg`, `--color-fg`, and related tokens in `:root` and a `[data-theme=dark]` selector.
**Files:** src/styles/tokens.css
### 2. Build the toggle component
Create a `<ThemeToggle>` button that switches `data-theme` on `<html>` and writes the choice to `localStorage`.
**Files:** src/components/ThemeToggle.tsx
### 3. Persist preference on load
Read `localStorage` on app init and apply the saved theme before first render to avoid a flash.
**Files:** src/main.tsx
## Constraints
Must not introduce a layout flash on initial load. No third-party theming libraries.
## Acceptance Criteria
- Toggle switches theme instantly
- Preference survives a page refresh
- Works in Chrome, Firefox, and Safari
