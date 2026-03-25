import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm, navigateToBrewList } from './fixtures'

test.describe('Delete Brew', () => {
  test('should delete a brew and remove from list', async ({ page }) => {
    // First, create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    // Verify brew is in list
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await expect(row).toBeVisible()

    // Click on the brew to go to detail page
    await row.click()
    await page.waitForURL('**/brew/**')

    // Click delete button
    await page.click('button:has-text("Delete")')

    // Confirm delete in dialog
    await page.click('button:has-text("Delete"), button:has-text("Confirm")')

    // Should be redirected to brews list
    await page.waitForURL('**/brews')

    // Verify brew is removed from list
    await expect(row).not.toBeVisible()
  })

  test('should cancel delete dialog and keep brew', async ({ page }) => {
    // First, create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log Brew")')
    await page.waitForURL('**/brews')

    // Verify brew is in list
    const row = page.locator('table tbody tr', { hasText: testBrewData.valid.bean })
    await expect(row).toBeVisible()

    // Click on the brew to go to detail page
    await row.click()
    await page.waitForURL('**/brew/**')

    // Click delete button
    await page.click('button:has-text("Delete")')

    // Cancel delete in dialog
    await page.click('button:has-text("Cancel")')

    // Should still be on detail page
    await expect(page).toHaveURL('**/brew/**')
    await expect(page.locator('h1')).toContainText(testBrewData.valid.bean)

    // Navigate back to list
    await page.click('a:has-text("Back to Brew Logs")')
    await page.waitForURL('**/brews')

    // Verify brew still exists in list
    await expect(row).toBeVisible()
  })
})
