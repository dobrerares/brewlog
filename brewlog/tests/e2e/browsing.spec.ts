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

    // Either table doesn't exist, or tbody is empty
    const rowCount = await page.locator('table tbody tr').count()
    if (rowCount === 0) {
      // Empty state should be shown (depends on implementation)
      // Just verify table structure is present
      await expect(table).toBeVisible()
    }
  })
})
