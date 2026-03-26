import { Page } from '@playwright/test'

export const testBrewData = {
  valid: {
    bean: 'Kenya AA',
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
    bean: 'Kenya AA',
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
    bean: 'Kenya AA',
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
    bean: 'Kenya AA',
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
    bean: 'Kenya AA',
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
  // Rating stars (SVG-based StarRating component)
  const stars = page.locator('[data-testid="star-rating"] button')
  for (let i = 0; i < brew.rating; i++) {
    await stars.nth(i).click()
  }
  if (brew.notes) {
    await page.fill('[name="notes"]', brew.notes)
  }
}

export async function navigateToNewBrewForm(page: Page) {
  await page.goto('/brew/new')
  await page.waitForURL(/\/brew\/new$/)
}

export async function navigateToBrewList(page: Page) {
  await page.goto('/brews')
  await page.waitForLoadState('networkidle')
}
