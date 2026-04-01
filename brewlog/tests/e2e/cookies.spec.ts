import { test, expect } from '@playwright/test'
import { dismissCookieBanner } from './fixtures'

test.describe('Cookie-Based Features', () => {
  test('should toggle theme and persist across page navigation', async ({ page }) => {
    await page.goto('/')
    await dismissCookieBanner(page)

    // Should start in light mode
    const html = page.locator('html')
    await expect(html).toHaveAttribute('data-theme', 'light')

    // Click theme toggle (moon icon = switch to dark)
    await page.click('button[aria-label="Switch to dark mode"]')
    await expect(html).toHaveAttribute('data-theme', 'dark')

    // Navigate to brews page - theme should persist
    await page.goto('/brews')
    await expect(html).toHaveAttribute('data-theme', 'dark')

    // Toggle back to light
    await page.click('button[aria-label="Switch to light mode"]')
    await expect(html).toHaveAttribute('data-theme', 'light')
  })

  test('should show cookie consent banner and dismiss it', async ({ page }) => {
    await page.goto('/')

    // Banner should be visible
    const banner = page.locator('text=We use cookies')
    await expect(banner).toBeVisible()

    // Accept cookies
    await page.click('button:has-text("Accept")')

    // Banner should disappear
    await expect(banner).not.toBeVisible()

    // Reload - banner should not reappear
    await page.reload()
    await expect(banner).not.toBeVisible()
  })

  test('should track last viewed brew and show continue link on landing', async ({ page }) => {
    // Go to brews list
    await page.goto('/brews')
    await dismissCookieBanner(page)
    await expect(page.locator('table tbody tr').first()).toBeVisible()

    // Click on the first brew via the row link
    const firstRow = page.locator('table tbody tr').first()
    await firstRow.locator('a').first().click()
    await page.waitForURL(/\/brew\/\w+/)

    // Get the bean name from detail page h1
    const beanName = await page.locator('h1').innerText()

    // Go to landing
    await page.goto('/')

    // Should show "Continue where you left off" with the bean name
    const continueLink = page.locator('a:has-text("Continue where you left off")')
    await expect(continueLink).toBeVisible()
    await expect(continueLink).toContainText(beanName)
  })

  test('should show activity stats on landing after browsing', async ({ page }) => {
    // Visit landing (this is visit 1)
    await page.goto('/')
    await dismissCookieBanner(page)

    // Visit brews page
    await page.goto('/brews')

    // Go back to landing (visit counter should now be > 0)
    await page.goto('/')

    // Landing should show welcome back message
    const activityText = page.locator('text=Welcome back')
    await expect(activityText).toBeVisible()
  })
})
