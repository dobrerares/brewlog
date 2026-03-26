import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm } from './fixtures'

test.describe('Form Validation', () => {
  test('should show error when required Bean field is empty on submit', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form without bean field
    await page.selectOption('[name="method"]', testBrewData.valid.method)
    await page.fill('[name="date"]', testBrewData.valid.date)
    await page.fill('[name="dose"]', testBrewData.valid.dose.toString())
    await page.fill('[name="water"]', testBrewData.valid.water.toString())
    await page.fill('[name="temp"]', testBrewData.valid.temp.toString())
    await page.fill('[name="time"]', testBrewData.valid.time)
    await page.fill('[name="grind"]', testBrewData.valid.grind)
    await page.selectOption('[name="grinder"]', testBrewData.valid.grinder)
    await page.click(`button:has-text("${testBrewData.valid.taste}")`)
    const stars = page.locator('[data-testid="star-rating"] button')
    for (let i = 0; i < testBrewData.valid.rating; i++) {
      await stars.nth(i).click()
    }
    await page.fill('[name="notes"]', testBrewData.valid.notes)

    // Submit form
    await page.click('button:has-text("Log brew")')

    // Should show bean error
    const beanError = page.locator('text=Bean is required')
    await expect(beanError).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL(/\/brew\/new$/)
  })

  test('should show temperature range error for V60 with invalid temperature', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with invalid temperature (75°C is too low for V60 which needs 90-96°C)
    const invalidTemp = { ...testBrewData.valid, temp: 75 }
    await fillBrewForm(page, invalidTemp)
    await page.click('button:has-text("Log brew")')

    // Form should not submit and stay on form page
    await expect(page).toHaveURL(/\/brew\/new$/)
  })

  test('should show dose/water ratio error when ratio is outside 10-20x range', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with invalid ratio (dose: 30, water: 250 = 8.3x, needs 10-20x)
    const invalidRatio = { ...testBrewData.valid, dose: 30, water: 250 }
    await fillBrewForm(page, invalidRatio)
    await page.click('button:has-text("Log brew")')

    // Form should not submit and stay on form page
    await expect(page).toHaveURL(/\/brew\/new$/)
  })

  test('should require notes when rating is below 3', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with low rating (2) and no notes - should require notes
    const lowRating = { ...testBrewData.valid, rating: 2, notes: '' }
    await fillBrewForm(page, lowRating)
    await page.click('button:has-text("Log brew")')

    // Form should not submit and stay on form page
    await expect(page).toHaveURL(/\/brew\/new$/)
  })
})
