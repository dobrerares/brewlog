# BrewLog

A coffee brewing journal built with React, TypeScript, and Tailwind CSS. Track every brew with precision — log beans, equipment, parameters, and taste notes. Visualize your brewing patterns with interactive charts that update live as you add, edit, or delete entries.

Built for **Systems for Design and Implementation: Assignment 1** (Bronze + Silver + Gold challenges).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 + TypeScript 5.9 |
| Routing | React Router 7 |
| Styling | Tailwind CSS 4 + CSS custom properties |
| Charts | Recharts 3 (PieChart, BarChart, RadarChart) |
| Icons | lucide-react |
| Build | Vite |
| Unit Tests | Vitest + @testing-library/react |
| E2E Tests | Playwright (Firefox — desktop + tablet) |
| Dev Env | NixOS flake.nix with Playwright Firefox patching |

## Getting Started

```bash
npm install
npm run dev          # Start dev server (http://localhost:5173)
```

### Running Tests

```bash
npm run test         # 80 unit tests (Vitest)
npm run test:e2e     # 32 e2e tests (Playwright)

# On NixOS — use the flake dev shell for Playwright:
nix develop --command bash -c "npx playwright test"
```

## Project Structure

```
src/
  App.tsx                        # Router — 8 routes
  index.css                      # Theme variables (light/dark), CSS animations
  app/
    pages/
      Landing.tsx                # Marketing page with activity stats
      Login.tsx                  # Email/password auth (cookie-based)
      Register.tsx               # Registration with password strength meter
      BrewList.tsx               # Master view — table (desktop) / cards (mobile)
      BrewDetail.tsx             # Detail view — parameters, rating, taste, notes
      BrewForm.tsx               # Create/edit form with real-time validation
      Statistics.tsx             # Dashboard — charts + data table side by side
    components/
      Navbar.tsx                 # Landing vs App variants, mobile hamburger
      Logo.tsx                   # Reusable branded logo
      StarRating.tsx             # Interactive/read-only star rating (SVG)
      TasteBadge.tsx             # Color-coded taste profile badge
      FlavorTag.tsx              # Selectable flavor tag pill
      DeleteConfirmModal.tsx     # Confirmation dialog for deletions
      ThemeToggle.tsx            # Light/dark mode toggle
      CookieConsent.tsx          # Cookie consent banner
    hooks/
      useBrewCRUD.ts             # In-memory CRUD store (create/read/update/delete)
      useBrewValidation.ts       # 10+ validation rules incl. cross-field
      useBrewPagination.ts       # Generic pagination
      useCookie.ts               # JSON cookie read/write (SameSite=Lax, 30-day)
      useTheme.ts                # Theme preference persistence
      useActivityTracker.ts      # Visit counting, last viewed brew tracking
      useAuth.ts                 # Cookie-based mock authentication
    data/
      mockData.ts                # 8 brews, 6 beans, 6 methods, 16 flavors
tests/
  e2e/
    fixtures.ts                  # Shared test data and helpers
    brew-logging.spec.ts         # Brew creation workflow
    browsing.spec.ts             # List/detail navigation
    delete.spec.ts               # Delete with confirm/cancel modal
    form-validation.spec.ts      # Field validation scenarios
    cookies.spec.ts              # Theme, consent, activity tracking
```

## Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Marketing page, activity stats, continue link |
| `/login` | Login | Email + password with field validation |
| `/register` | Register | Name/email/password + strength indicator |
| `/brews` | BrewList | Paginated master list with delete actions |
| `/brew/new` | BrewForm | Create new brew log |
| `/brew/:id` | BrewDetail | View brew parameters, rating, notes |
| `/brew/:id/edit` | BrewForm | Edit existing brew |
| `/dashboard` | Statistics | Charts + interactive data table side by side |

---

## Bronze Challenge

### Unit Tests (80 tests, 6 files)

All important CRUD operations and hooks are covered:

| Hook | What's Tested |
|------|--------------|
| `useBrewCRUD` | Create, read all, read by ID, update, delete, ID generation, not-found |
| `useBrewValidation` | Required fields, numeric ranges, ratio 10-20x, method-specific temps, low rating requires notes |
| `useBrewPagination` | Page boundaries, next/prev, goToPage, edge cases |
| `useCookie` | Set/get/remove, JSON serialization, SameSite |
| `useTheme` | Toggle, persistence, document attribute |
| `useActivityTracker` | Visit counting, last viewed, brew log counting |

### Client-Side Validation

`useBrewValidation` enforces:

- **Required fields**: bean, method, date, dose, water, temp, time, grind, grinder, rating, taste
- **Numeric ranges**: dose > 0, water > 0, temp 80-100, rating 1-5
- **Cross-field**: dose/water ratio must be 10-20x
- **Method-specific temps**: V60/Chemex 90-96, Espresso 85-100, French Press 92-96, AeroPress 80-95
- **Conditional**: rating < 3 requires notes explaining what went wrong

All forms show errors on blur (touched fields only) and on submit.

---

## Silver Challenge

### Playwright E2E Tests (32 tests, 5 files)

Each test runs on two viewports: `firefox-desktop` (1920x1080) and `firefox-tablet` (768x1024).

| Feature | File | Scenarios |
|---------|------|-----------|
| Brew creation | `brew-logging.spec.ts` | Valid brew creation, empty submit errors, invalid field errors |
| Navigation | `browsing.spec.ts` | List to detail, back navigation, empty state |
| Deletion | `delete.spec.ts` | Delete + modal confirm, cancel keeps brew |
| Form validation | `form-validation.spec.ts` | Missing bean, bad temp, bad ratio, low rating |
| Cookie features | `cookies.spec.ts` | Theme persistence, consent banner, last viewed brew, activity stats |

### Cookie-Based Monitoring

| Cookie | Purpose | Hook |
|--------|---------|------|
| `brewlog_theme` | Light/dark mode preference | `useTheme` |
| `brewlog_visits` | Page visit counts (path to count map) | `useActivityTracker` |
| `brewlog_last_viewed` | Last viewed brew ID + bean name | `useActivityTracker` |
| `brewlog_user` | Auth session (name + email) | `useAuth` |
| `brewlog_cookie_consent` | Banner dismissal state | `CookieConsent` |

All cookies go through `useCookie` — a generic hook with JSON serialization, `SameSite=Lax`, and 30-day `max-age`.

The Landing page shows personalized messages: "Welcome back! You've visited X times and logged Y brews" and "Continue where you left off" linking to the last viewed brew.

---

## Gold Challenge

### All Figma Pages with Transitions

7 pages with full navigation flow:

```
Login/Register --> Landing --> BrewList (master) --> BrewDetail --> BrewForm (edit)
                                  |                                     ^
                                  +---> BrewForm (new) ----------------+
                                  |
                                  +---> Dashboard (charts + table)
```

Shared `Navbar` component with two variants: `type="landing"` (Log in / Sign up) and `type="app"` (Brew Logs / Dashboard + avatar/logout).

### Side-by-Side Views Synced with CRUD

The Dashboard page shows charts and an interactive data table **simultaneously**:

```
+---------------------------+---------------------------+
|  CHARTS (left)            |  DATA TABLE (right)       |
|                           |                           |
|  Brewing Methods PieChart |  All Brews                |
|  Taste Distribution Bar   |  [bean] [method] [rating] |
|  Rating Distribution Bar  |  [edit]  [delete]         |
|                           |                           |
|                           |  Bean Rankings            |
+---------------------------+---------------------------+
|         Brew DNA RadarChart (full width)               |
+-------------------------------------------------------+
```

Both columns read from `useBrewCRUD().getBrews()`. Deleting a row from the table instantly recomputes all chart distributions. Adding or editing brews (via form links) updates both views on return.

Layout: `grid grid-cols-1 lg:grid-cols-2` — side by side on desktop, stacked vertically on mobile.

### Responsive Design

| Component | Mobile (<640px) | Desktop |
|-----------|----------------|---------|
| BrewList | Card layout | Table with columns |
| Navbar | Hamburger menu | Full nav links |
| BrewForm | Single column | 2-col / 3-col grids |
| Dashboard | Charts above table | Side by side |
| Summary cards | 1 column | 3 columns |
| Landing CTAs | Stacked buttons | Side by side |

### Animations and Visual Effects

| Animation | Effect | Used In |
|-----------|--------|---------|
| `fadeIn` | Opacity + translateY (0.4s) | Landing, forms, cards, dashboard |
| `scaleIn` | Scale 0.95 to 1 (0.3s) | Delete confirmation modal |
| `slideDown` | TranslateY reveal (0.3s) | Mobile navigation menu |
| Theme transition | Background/color 0.3s ease | Entire page on theme toggle |
| Hover effects | Opacity, scale-110 | Table rows, star rating, buttons |
| Password strength | Width transition 0.3s | Register page progress bar |

Dark mode uses CSS custom properties with smooth transitions — toggling theme smoothly animates all backgrounds, text colors, and borders.

---

## Test Results

```
Unit Tests:  80 passed  (6 test files)
E2E Tests:   32 passed  (5 test files x 2 viewports)
TypeScript:  0 errors
```
