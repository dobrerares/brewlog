# Cookie-Based User Activity & Preference Monitoring — Design

## Goal

Implement a cookie-based system for monitoring user activity and preferences in the browser, satisfying the Silver challenge requirement.

## Features

### 1. Theme Preference (dark/light mode)
- Cookie: `brewlog_theme` — stores `"light"` or `"dark"`
- 30-day expiry, `SameSite=Lax`, `path=/`
- Toggle button in nav bar across all pages
- Applied via existing CSS custom properties (`--background`, `--foreground`, etc.)

### 2. Last Viewed Brew
- Cookie: `brewlog_last_viewed` — stores JSON `{"id": "...", "bean": "..."}`
- Set on BrewDetail page mount
- Landing page shows "Continue where you left off → {bean name}" link
- Gracefully handles deleted brews (link not shown if brew no longer exists)

### 3. Page Visit Counter
- Cookie: `brewlog_visits` — stores JSON object `{"/brews": 5, "/brew/new": 3, ...}`
- Incremented on each route change
- Landing page shows activity summary: "You've logged X brews and browsed Y times"
- 30-day expiry

### 4. Cookie Consent Banner
- Shown once on first visit
- Acceptance stored in `brewlog_consent` cookie
- Dismissable, non-blocking

## Architecture

### Hooks
- `useCookie(name, defaultValue, options)` — generic get/set/delete wrapping `document.cookie`
- `useTheme()` — dark/light toggle backed by `useCookie`
- `useActivityTracker()` — visit counting + last viewed brew, backed by `useCookie`

### Components
- `ThemeToggle` — sun/moon icon button for nav
- `CookieConsent` — bottom banner with accept button
- Activity summary section on Landing page

### Cookie Format
All cookies use: `path=/; SameSite=Lax; max-age=2592000` (30 days).
No `Secure` flag (dev runs on localhost HTTP).

## Dark Theme

New CSS variables for dark mode, toggled by a `[data-theme="dark"]` attribute on `<html>`:

```css
[data-theme="dark"] {
  --background: #1a1612;
  --foreground: #e8e0d8;
  --card: #2a2420;
  --border-color: #3a3430;
  --text-muted: #a09890;
  --cream: #2a2420;
  --primary-brown: #c4956a;
  --primary-dark: #e8d0b8;
}
```

## Testing

- Unit tests for `useCookie` hook (set, get, delete, expiry, JSON values)
- E2e test: toggle theme, reload, verify persistence
- E2e test: view a brew, go to landing, verify "continue" link appears
