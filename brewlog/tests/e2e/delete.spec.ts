import { test, expect } from '@playwright/test'
import { testBrewData, fillBrewForm, navigateToNewBrewForm, findBrewRowAcrossPages } from './fixtures'

test.describe('Delete Brew', () => {
  test('should delete a brew and remove from list', async ({ page }) => {
    // First, create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log brew")')
    await page.waitForURL(/\/brews$/)

    // Verify brew is in list
    const row = await findBrewRowAcrossPages(page, new RegExp(`${testBrewData.valid.bean}.*V60`))
    await expect(row).toBeVisible()

    // Click on the brew to go to detail page
    await row.locator('a').first().click()
    await page.waitForURL(/\/brew\/\w+/)

    // Click Delete button on detail page to open modal
    await page.click('button:has-text("Delete")')

    // Wait for the confirmation modal to appear
    await page.locator('text=Delete brew log?').waitFor({ state: 'visible' })

    // Confirm deletion by clicking the modal's Delete button
    await page.locator('.fixed.z-50 button:has-text("Delete")').click()

    // Should be redirected to brews list
    await page.waitForURL(/\/brews$/)

    // Verify brew is removed from list
    await expect(row).not.toBeVisible()
  })

  test('should cancel delete dialog and keep brew', async ({ page }) => {
    // First, create a brew
    await navigateToNewBrewForm(page)
    await fillBrewForm(page, testBrewData.valid)
    await page.click('button:has-text("Log brew")')
    await page.waitForURL(/\/brews$/)

    // Verify brew is in list
    const row = await findBrewRowAcrossPages(page, new RegExp(`${testBrewData.valid.bean}.*V60`))
    await expect(row).toBeVisible()

    // Click on the brew to go to detail page
    await row.locator('a').first().click()
    await page.waitForURL(/\/brew\/\w+/)

    // Click Delete button on detail page to open modal
    await page.click('button:has-text("Delete")')

    // Wait for the confirmation modal to appear
    await page.locator('text=Delete brew log?').waitFor({ state: 'visible' })

    // Cancel by clicking Cancel button in modal
    await page.locator('.fixed.z-50 button:has-text("Cancel")').click()

    // Should still be on detail page
    await expect(page).toHaveURL(/\/brew\/\w+/)
    await expect(page.locator('h1')).toContainText(testBrewData.valid.bean)

    // Navigate back to list
    await page.click('a:has-text("Back to brew logs")')
    await page.waitForURL(/\/brews$/)

    // Verify brew still exists in list
    await expect(row).toBeVisible()
  })
})
