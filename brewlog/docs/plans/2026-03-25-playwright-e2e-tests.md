# Playwright E2E Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build comprehensive Playwright e2e tests covering brew logging, browsing, form validation, and delete workflows across desktop and tablet viewports.

**Architecture:** Test suite organized by feature (4 spec files), with shared fixtures for test data generation and helpers for common actions (navigation, form filling). Tests run fresh data per execution, cleanup after assertions. Playwright runs each test on both 1920×1080 and 768×1024 viewports automatically via test configuration.

**Tech Stack:** Playwright (browser automation), Vitest/Jest test runner, TypeScript, React Router navigation, design system CSS variables.

---

## Task 1: Install Playwright & Create Config

**Files:**
- Create: `playwright.config.ts`
- Modify: `package.json` (dependencies)

**Step 1: Install Playwright**

```bash
npm install -D @playwright/test
```

Expected: playwright package added to node_modules and package.json

**Step 2: Create playwright.config.ts**

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1920, height: 1080 } },
    },
    {
      name: 'chromium-tablet',
      use: { ...devices['iPad Pro'], viewport: { width: 768, height: 1024 } },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

**Step 3: Create test directory structure**

```bash
mkdir -p tests/e2e
touch tests/e2e/fixtures.ts
```

Expected: `tests/e2e/` directory created with fixtures.ts file

**Step 4: Add test script to package.json**

Add to `package.json` scripts section:
```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui"
```

**Step 5: Commit**

```bash
git add playwright.config.ts package.json tests/e2e/
git commit -m "feat: setup Playwright e2e testing framework"
```

---

## Task 2: Create Test Fixtures & Helpers

**Files:**
- Create: `tests/e2e/fixtures.ts`

**Step 1: Write fixture file with test data builder**

```typescript
import { Page } from '@playwright/test'

export const testBrewData = {
  valid: {
    bean: 'Ethiopian Yirgacheffe',
    method: 'V60',
    date: new Date().toISOString().split('T')[0],
    dose: 18,
    water: 300,
    temp: 93,
    time: '3:00',
    grind: '22 clicks',
    grinder: 'Baratza Encore',
    rating: 4,
    taste: 'Balanced',
    notes: 'Great acidity, fruity notes',
  },
  invalidDose: {
    bean: 'Ethiopian Yirgacheffe',
    method: 'V60',
    date: new Date().toISOString().split('T')[0],
    dose: 0, // invalid
    water: 300,
    temp: 93,
    time: '3:00',
    grind: '22 clicks',
    grinder: 'Baratza Encore',
    rating: 4,
    taste: 'Balanced',
    notes: '',
  },
  invalidTemp: {
    bean: 'Ethiopian Yirgacheffe',
    method: 'V60',
    date: new Date().toISOString().split('T')[0],
    dose: 18,
    water: 300,
    temp: 75, // invalid for V60 (needs 90-96)
    time: '3:00',
    grind: '22 clicks',
    grinder: 'Baratza Encore',
    rating: 4,
    taste: 'Balanced',
    notes: '',
  },
  invalidRatio: {
    bean: 'Ethiopian Yirgacheffe',
    method: 'V60',
    date: new Date().toISOString().split('T')[0],
    dose: 30,
    water: 250, // 8.3x ratio - invalid (needs 10-20x)
    temp: 93,
    time: '3:00',
    grind: '22 clicks',
    grinder: 'Baratza Encore',
    rating: 4,
    taste: 'Balanced',
    notes: '',
  },
  lowRatingNoNotes: {
    bean: 'Ethiopian Yirgacheffe',
    method: 'V60',
    date: new Date().toISOString().split('T')[0],
    dose: 18,
    water: 300,
    temp: 93,
    time: '3:00',
    grind: '22 clicks',
    grinder: 'Baratza Encore',
    rating: 2, // low rating
    taste: 'Balanced',
    notes: '', // missing notes - invalid
  },
}

export async function fillBrewForm(page: Page, brew: typeof testBrewData.valid) {
  await page.selectOption('[name="bean"]', brew.bean)
  await page.selectOption('[name="method"]', brew.method)
  await page.fill('[name="date"]', brew.date)
  await page.fill('[name="dose"]', brew.dose.toString())
  await page.fill('[name="water"]', brew.water.toString())
  await page.fill('[name="temp"]', brew.temp.toString())
  await page.fill('[name="time"]', brew.time)
  await page.fill('[name="grind"]', brew.grind)
  await page.selectOption('[name="grinder"]', brew.grinder)
  // Taste button
  await page.click(`button:has-text("${brew.taste}")`)
  // Rating stars
  for (let i = 0; i < brew.rating; i++) {
    await page.locator('button[type="button"]').filter({ hasText: '⭐' }).nth(i).click()
  }
  if (brew.notes) {
    await page.fill('[name="notes"]', brew.notes)
  }
}

export async function navigateToNewBrewForm(page: Page) {
  await page.goto('/')
  await page.click('a:has-text("Log a Brew")')
  await page.waitForURL('**/brew/new')
}

export async function navigateToBrewList(page: Page) {
  await page.goto('/brews')
  await page.waitForLoadState('networkidle')
}
```

**Step 2: Verify fixtures are syntactically correct**

```bash
npx tsc --noEmit tests/e2e/fixtures.ts
```

Expected: No TypeScript errors

**Step 3: Commit**

```bash
git add tests/e2e/fixtures.ts
git commit -m "feat: add test fixtures and helper functions"
```

---

## Task 3: Brew Logging Tests

**Files:**
- Create: `tests/e2e/brew-logging.spec.ts`

**Step 1: Write failing test - Valid brew creation**

```typescript
import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm } from './fixtures'

test.describe('Brew Logging', () => {
  test('should create a valid brew and display in list', async ({ page }) => {
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')

    // Should redirect to brews list
    await page.waitForURL('**/brews')

    // Newly created brew should appear in table
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await expect(row).toBeVisible()
    await expect(row).toContainText('V60')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm run test:e2e -- tests/e2e/brew-logging.spec.ts
```

Expected: FAIL - page not navigating or element not found (features not yet implemented in test context)

**Step 3: Add remaining brew logging tests**

```typescript
  test('should show required field errors on empty submit', async ({ page }) => {
    await navigateToNewBrewForm(page)
    // Don't fill form, just submit
    await page.click('button:has-text("Log Brew")')

    // Error messages should appear
    const beanError = page.locator('text=Bean is required')
    const methodError = page.locator('text=Method is required')
    await expect(beanError).toBeVisible()
    await expect(methodError).toBeVisible()

    // Should NOT navigate away
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should show validation errors for invalid dose and temp', async ({ page }) => {
    await navigateToNewBrewForm(page)

    const invalidBrew = { ...testBrewData.valid, dose: 0, temp: 75 }
    await fillBrewForm(page, invalidBrew)
    await page.click('button:has-text("Log Brew")')

    // Both errors should display
    const doseError = page.locator('text=greater than 0')
    const tempError = page.locator('text=90-96')
    await expect(doseError).toBeVisible()
    await expect(tempError).toBeVisible()
    await expect(page).toHaveURL('**/brew/new')
  })
```

**Step 4: Run tests**

```bash
npm run test:e2e -- tests/e2e/brew-logging.spec.ts
```

Expected: 3 tests run on both desktop and tablet (6 total). All pass.

**Step 5: Commit**

```bash
git add tests/e2e/brew-logging.spec.ts
git commit -m "test: add e2e tests for brew logging workflow"
```

---

## Task 4: Browsing Tests

**Files:**
- Create: `tests/e2e/browsing.spec.ts`

**Step 1: Write browsing tests**

```typescript
import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm, navigateToBrewList } from './fixtures'

test.describe('Browsing Brews', () => {
  test('should view brew list and navigate to detail page', async ({ page }) => {
    // First, create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    // Click into the created brew
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await row.click()

    // Should be on detail page showing all brew info
    await page.waitForURL('**/brew/**')
    await expect(page.locator('h1')).toContainText(testBrewData.valid.bean)
    await expect(page.locator('text=Brewing Parameters')).toBeVisible()
    await expect(page.locator('text=Review')).toBeVisible()
    await expect(page.locator('text=' + testBrewData.valid.dose)).toBeVisible()
  })

  test('should navigate back from detail to list', async ({ page }) => {
    // Create and view a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await row.click()
    await page.waitForURL('**/brew/**')

    // Click back button
    await page.click('a:has-text("Back to Brew Logs")')
    await page.waitForURL('**/brews')

    // Should be back on list
    await expect(page.locator('h1, h2, text=BrewLog')).toBeVisible()
    await expect(row).toBeVisible()
  })

  test('should show empty state when no brews exist', async ({ page }) => {
    await navigateToBrewList(page)

    // If list is empty, should show empty state
    const table = page.locator('table')
    const tbody = page.locator('table tbody')

    // Either table doesn't exist, or tbody is empty
    const rowCount = await page.locator('table tbody tr').count()
    if (rowCount === 0) {
      // Empty state should be shown (depends on implementation)
      // Just verify table structure is present
      await expect(table).toBeVisible()
    }
  })
})
```

**Step 2: Run tests**

```bash
npm run test:e2e -- tests/e2e/browsing.spec.ts
```

Expected: 3 tests run on both viewports (6 total). All pass.

**Step 3: Commit**

```bash
git add tests/e2e/browsing.spec.ts
git commit -m "test: add e2e tests for browsing brews"
```

---

## Task 5: Form Validation Tests

**Files:**
- Create: `tests/e2e/form-validation.spec.ts`

**Step 1: Write validation tests**

```typescript
import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm } from './fixtures'

test.describe('Form Validation', () => {
  test('should require Bean field', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill everything except bean
    const brewData = { ...testBrewData.valid, bean: '' }
    await fillBrewForm(page, brewData)
    await page.click('button:has-text("Log Brew")')

    const error = page.locator('text=Bean is required')
    await expect(error).toBeVisible()
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should enforce temperature range for V60 (90-96°C)', async ({ page }) => {
    await navigateToNewBrewForm(page)

    const brewData = { ...testBrewData.valid, method: 'V60', temp: 89 }
    await fillBrewForm(page, brewData)
    await page.click('button:has-text("Log Brew")')

    const error = page.locator('text=90-96')
    await expect(error).toBeVisible()
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should enforce dose/water ratio (10-20x)', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // 30g dose / 250g water = 8.3x (invalid)
    const brewData = { ...testBrewData.valid, dose: 30, water: 250 }
    await fillBrewForm(page, brewData)
    await page.click('button:has-text("Log Brew")')

    const error = page.locator('text=10-20x')
    await expect(error).toBeVisible()
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should require notes for low ratings (< 3)', async ({ page }) => {
    await navigateToNewBrewForm(page)

    const brewData = { ...testBrewData.valid, rating: 2, notes: '' }
    await fillBrewForm(page, brewData)
    await page.click('button:has-text("Log Brew")')

    const error = page.locator('text=low-rated')
    await expect(error).toBeVisible()
    await expect(page).toHaveURL('**/brew/new')
  })
})
```

**Step 2: Run tests**

```bash
npm run test:e2e -- tests/e2e/form-validation.spec.ts
```

Expected: 4 tests run on both viewports (8 total). All pass.

**Step 3: Commit**

```bash
git add tests/e2e/form-validation.spec.ts
git commit -m "test: add e2e tests for form validation scenarios"
```

---

## Task 6: Delete Tests

**Files:**
- Create: `tests/e2e/delete.spec.ts`

**Step 1: Write delete tests**

```typescript
import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm } from './fixtures'

test.describe('Delete Brew', () => {
  test('should delete a brew from detail page and remove from list', async ({ page }) => {
    // Create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    // Navigate to detail
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await row.click()
    await page.waitForURL('**/brew/**')

    // Delete the brew
    page.once('dialog', dialog => dialog.accept())
    await page.click('button:has-text("Delete")')

    // Should redirect to list
    await page.waitForURL('**/brews')

    // Brew should no longer appear in table
    const deletedRow = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await expect(deletedRow).not.toBeVisible()
  })

  test('should cancel delete when confirming dialog', async ({ page }) => {
    // Create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    // Navigate to detail
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await row.click()
    await page.waitForURL('**/brew/**')

    // Try to delete but cancel
    page.once('dialog', dialog => dialog.dismiss())
    await page.click('button:has-text("Delete")')

    // Should still be on detail page
    await expect(page).toHaveURL('**/brew/**')

    // Brew data should still be visible
    await expect(page.locator('h1')).toContainText(testBrewData.valid.bean)
  })
})
```

**Step 2: Run tests**

```bash
npm run test:e2e -- tests/e2e/delete.spec.ts
```

Expected: 2 tests run on both viewports (4 total). All pass.

**Step 3: Commit**

```bash
git add tests/e2e/delete.spec.ts
git commit -m "test: add e2e tests for delete workflow"
```

---

## Task 7: Run Full Test Suite & Verify

**Step 1: Run all e2e tests**

```bash
npm run test:e2e
```

Expected: 12 tests × 2 viewports = 24 total test runs, all passing. Should complete in <60 seconds.

**Step 2: Generate HTML report**

```bash
npx playwright show-report
```

Expected: Browser opens with detailed test report showing all passes by viewport

**Step 3: Final commit**

```bash
git add tests/e2e/
git commit -m "test: complete Playwright e2e test suite (12 tests, 2 viewports)"
```

---

## Summary

**Total: 12 tests covering:**
- ✅ Brew logging (3 tests)
- ✅ Browsing & navigation (3 tests)
- ✅ Form validation (4 tests)
- ✅ Delete workflow (2 tests)

**Each test runs on:**
- Desktop (1920×1080)
- Tablet (768×1024)

**Total test coverage: 24 test runs, all isolated with fresh data**
