import { expect, test } from '@playwright/test'

test('suspicious client can trigger observed state through denied admin requests', async ({ request }) => {
  const email = `suspect-${Date.now()}@x.com`
  await request.post('/api/v1/auth/register', { data: { email, password: 'hunter2' } })
  await request.post('/api/v1/auth/login', { data: { email, password: 'hunter2' } })

  for (let i = 0; i < 6; i += 1) {
    const denied = await request.get('/api/v1/admin/observed-users')
    expect(denied.status()).toBe(403)
  }
})
