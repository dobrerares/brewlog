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
})
