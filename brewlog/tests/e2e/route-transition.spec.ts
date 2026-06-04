import { expect, test, type Page } from '@playwright/test'

async function routeShellOpacity(page: Page) {
  return page.evaluate(() => {
    return new Promise<number>((resolve) => {
      requestAnimationFrame(() => {
        const shells = [...document.querySelectorAll<HTMLElement>('.route-shell')]
          .filter((element) => element.isConnected)

        if (shells.length === 0) {
          resolve(0)
          return
        }

        resolve(Math.max(...shells.map((element) => Number(window.getComputedStyle(element).opacity))))
      })
    })
  })
}

async function minimumAnimatedOpacity(page: Page) {
  return page.evaluate(() => {
    const animated = [
      ...document.querySelectorAll('.animate-fadeIn, .animate-scaleIn, .animate-slideDown'),
    ].filter((element) => {
      const rect = element.getBoundingClientRect()
      return rect.width > 0 && rect.height > 0
    })

    if (animated.length === 0) return 1

    return Math.min(
      ...animated.map((element) => Number(window.getComputedStyle(element).opacity))
    )
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

  expect(Math.min(...samples), `route-shell opacity samples: ${samples.join(', ')}`).toBeGreaterThan(0.9)

  const otherTab = await context.newPage()
  await otherTab.goto('about:blank')

  await page.bringToFront()
  await page.getByRole('link', { name: 'Brew Logs' }).click({ noWaitAfter: true })
  await otherTab.bringToFront()
  await otherTab.waitForTimeout(250)
  await page.bringToFront()

  expect(await routeShellOpacity(page)).toBeGreaterThan(0.9)
})

test('keeps animated page content visible if a browser tab switch interrupts entry', async ({ page, context }) => {
  const otherTab = await context.newPage()
  await otherTab.goto('about:blank')

  for (const path of ['/login', '/register', '/password-reset']) {
    await page.bringToFront()
    await page.goto(path, { waitUntil: 'commit' })
    await otherTab.bringToFront()
    await otherTab.waitForTimeout(50)
    await page.bringToFront()

    expect(await minimumAnimatedOpacity(page)).toBeGreaterThan(0.9)
  }
})
