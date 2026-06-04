import { expect, test, type Page } from '@playwright/test'

async function routeShellOpacity(page: Page) {
  return page.locator('.route-shell').evaluate((element) => {
    return Number(window.getComputedStyle(element).opacity)
  })
}

test('keeps the app visible while switching routes and browser tabs', async ({ page, context }) => {
  await page.goto('/brews')
  await expect(page.getByRole('heading', { name: 'Brew Logs' })).toBeVisible()

  const samples: number[] = []
  await page.getByRole('link', { name: 'Dashboard' }).click({ noWaitAfter: true })

  let previousElapsed = 0
  for (const elapsed of [0, 50, 100, 170, 240, 320]) {
    await page.waitForTimeout(elapsed - previousElapsed)
    previousElapsed = elapsed
    samples.push(await routeShellOpacity(page))
  }

  expect(Math.min(...samples)).toBeGreaterThan(0.9)

  const otherTab = await context.newPage()
  await otherTab.goto('about:blank')

  await page.bringToFront()
  await page.getByRole('link', { name: 'Brew Logs' }).click({ noWaitAfter: true })
  await otherTab.bringToFront()
  await otherTab.waitForTimeout(250)
  await page.bringToFront()

  expect(await routeShellOpacity(page)).toBeGreaterThan(0.9)
})
