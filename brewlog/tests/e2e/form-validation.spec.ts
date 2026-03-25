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
    for (let i = 0; i < testBrewData.valid.rating; i++) {
      await page.locator('button[type="button"]').filter({ hasText: '⭐' }).nth(i).click()
    }
    await page.fill('[name="notes"]', testBrewData.valid.notes)

    // Submit form
    await page.click('button:has-text("Log Brew")')

    // Should show bean error
    const beanError = page.locator('text=Bean is required')
    await expect(beanError).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should show temperature range error for V60 with invalid temperature', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with invalid temperature
    await fillBrewForm(page, testBrewData.invalidTemp)
    await page.click('button:has-text("Log Brew")')

    // Should show temperature range error (90-96°C for V60)
    const tempError = page.locator('text=/V60.*90.*96|temperature.*90.*96/i')
    await expect(tempError).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should show dose/water ratio error when ratio is outside 10-20x range', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with invalid ratio (dose: 30, water: 250 = 8.3x)
    await fillBrewForm(page, testBrewData.invalidRatio)
    await page.click('button:has-text("Log Brew")')

    // Should show ratio error (10-20x range)
    const ratioError = page.locator('text=/ratio|10.*20|dose.*water/i')
    await expect(ratioError).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL('**/brew/new')
  })

  test('should require notes when rating is below 3', async ({ page }) => {
    await navigateToNewBrewForm(page)

    // Fill form with low rating and no notes
    await fillBrewForm(page, testBrewData.lowRatingNoNotes)
    await page.click('button:has-text("Log Brew")')

    // Should show notes required error
    const notesError = page.locator('text=/notes.*required|low.*rating|must.*provide.*notes/i')
    await expect(notesError).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL('**/brew/new')
  })
})
