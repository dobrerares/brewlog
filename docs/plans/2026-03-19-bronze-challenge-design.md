# BrewLog Bronze Challenge Design

**Goal:** Implement master/detail CRUD views with strict validation and ~80% test coverage within 1 week.

**Architecture:** Three-layer separation (UI components → custom hooks with logic → in-memory mock data). Components never touch data directly; all business logic lives in hooks.

**Tech Stack:** React 18 + TypeScript + Tailwind CSS + Radix UI + React Testing Library

---

## Architecture Overview

**Three-layer separation:**
- **UI Layer** — React components (Landing, BrewList, BrewDetail, BrewForm)
- **Logic Layer** — Custom hooks (useBrewValidation, useBrewCRUD, useBrewPagination)
- **Data Layer** — mockData.ts (in-memory store)

**Data flow:**
```
Component (UI)
  ↓ (calls hooks)
Custom Hooks (validation + CRUD logic)
  ↓ (updates)
Mock Data (BrewLog[] in RAM)
  ↓ (re-renders)
Component (UI)
```

---

## Validation Strategy (Strict Level)

**Three validation layers:**

1. **Field-level validation** (real-time):
   - Required fields: bean, method, date, dose, water, temp, time, grind, rating, taste
   - Numeric ranges: dose > 0, water > 0, temp 80-100°C, rating 1-5
   - Enum constraints: method/bean/grinder/brewer must match allowed lists
   - Format: brew time must be MM:SS format
   - Yield must be positive (if provided)

2. **Business rule validation** (form submission):
   - dose/water ratio: water should be 10-20x dose (coffee brewing standard)
   - Temp-to-method: espresso requires temp >85°C, pour-over 90-96°C, cold brew N/A
   - Grind adjustment: if provided, must have direction + clicks + newSetting

3. **Cross-field validation**:
   - If taste is "Sour" and grind is fine → suggest coarser grind
   - If rating < 3 → require grindAdjustment notes

**Custom hook: `useBrewValidation.ts`**
- `validateField(name, value)` → errors for each field
- `validateForm(brewData)` → all errors at once
- `getValidationErrors()` → object with all field errors
- Used in BrewForm for real-time feedback + submission blocking

---

## CRUD Operations

**Custom hook: `useBrewCRUD.ts`**
- State: brews (BrewLog[]), currentBrew (BrewLog | null)
- Actions:
  - `createBrew(data)` → adds to brews, returns success/error
  - `updateBrew(id, data)` → updates brew by id
  - `deleteBrew(id)` → removes brew
  - `getBrew(id)` → fetches single brew for detail view
  - `getBrews()` → returns all brews

Forms call these hooks; components listen to state changes.

---

## Pagination

**Custom hook: `useBrewPagination.ts`**
- Props: items (BrewLog[]), pageSize (10)
- Returns: currentPage, totalPages, currentItems, goToPage(n), nextPage(), prevPage()
- BrewList uses this to paginate brew table

---

## Component Structure

**Landing** ✅
- Shows: logo + "BrewLog" name + tagline + brief description
- No changes needed

**BrewList** ⚠️
- Add pagination using `useBrewPagination` hook
- Display paginated brew table (date, bean, method, rating, taste)
- "New Brew" button → navigate to BrewForm
- "Edit" button on each row → navigate to BrewForm with :id
- "Delete" button → calls `useBrewCRUD.deleteBrew()`

**BrewDetail** ⚠️
- Shows full brew info
- "Edit" button → navigate to BrewForm
- "Delete" button → navigate back to BrewList

**BrewForm** 🔴
- Use `useBrewValidation` for real-time validation
- Use `useBrewCRUD` for create/update
- Show validation errors below each field
- Block form submission if errors exist
- On submit: validate → if valid, createBrew/updateBrew → navigate to BrewList
- On cancel: navigate back

---

## Testing Strategy (~80% coverage)

**Unit tests:**
- `useBrewValidation.test.ts` — All field validations, business rules, cross-field rules
- `useBrewCRUD.test.ts` — Add, update, delete operations

**Integration tests:**
- BrewForm submit flow: fill → validate → save → redirect
- BrewList delete flow: delete → brew removed
- BrewList pagination: navigate pages → correct brews shown

**Component tests:**
- BrewList renders table + pagination
- BrewForm shows validation errors

---

## Separation of Concerns

| Layer | Responsibility | Location |
|-------|---|---|
| **Data** | In-memory brew storage | `src/app/data/mockData.ts` |
| **Validation Logic** | Validate fields, business rules | `src/app/hooks/useBrewValidation.ts` |
| **CRUD Logic** | Create, read, update, delete | `src/app/hooks/useBrewCRUD.ts` |
| **Pagination Logic** | Paginate arrays | `src/app/hooks/useBrewPagination.ts` |
| **UI Components** | Render forms, lists, details | `src/app/pages/*`, `src/app/components/*` |

---

## Deliverables

✅ Landing page with logo, name, tagline, description
✅ Master view — paginated brew table (10 items/page)
✅ Detail view — full brew info
✅ Create — BrewForm with strict validation
✅ Update — BrewForm for editing
✅ Delete — delete button with confirmation
✅ Validation — field + business rule + cross-field
✅ Tests — ~80% coverage (unit + integration)
✅ Separation — logic in hooks, UI in components
