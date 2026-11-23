const test = require('node:test');
const assert = require('node:assert/strict');
const request = require('supertest');
const app = require('../src/app');

test('GET /health returns 200 and healthy status', async () => {
  const res = await request(app).get('/health');
  assert.equal(res.status, 200);
  assert.equal(res.body.status, 'healthy');
  assert.equal(res.body.service, 'arkastra-backend');
});

test('GET /api/dashboard/overview returns overview telemetry', async () => {
  const res = await request(app).get('/api/dashboard/overview');
  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(res.body.currentConditions);
  assert.ok(res.body.latestForecast);
  assert.ok(Array.isArray(res.body.recentEvents));
});

test('GET /api/dashboard/current-flux returns valid flux values', async () => {
  const res = await request(app).get('/api/dashboard/current-flux');
  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(res.body.longFlux > 0);
  assert.ok(res.body.activityClassification);
});

test('GET /api/solar/events returns flare events', async () => {
  const res = await request(app).get('/api/solar/events?limit=5');
  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(Array.isArray(res.body.events));
});

test('GET /api/forecast/history returns paginated forecasts', async () => {
  const res = await request(app).get('/api/forecast/history?limit=10');
  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(Array.isArray(res.body.items));
  assert.ok(res.body.total >= 0);
});

test('GET /api/model/metrics returns scientific evaluation report', async () => {
  const res = await request(app).get('/api/model/metrics');
  assert.equal(res.status, 200);
  assert.ok(res.body.calibrated_model_metrics);
  assert.ok(res.body.calibrated_model_metrics.brier_skill_score !== undefined);
});

test('POST /api/auth/register and /api/auth/login user authentication flow', async () => {
  const testEmail = `test_${Date.now()}@arkastra.org`;
  const regRes = await request(app).post('/api/auth/register').send({
    name: 'Astrophysics Researcher',
    email: testEmail,
    password: 'secure_password_123',
    role: 'researcher',
  });
  assert.equal(regRes.status, 201);
  assert.ok(regRes.body.token);

  const loginRes = await request(app).post('/api/auth/login').send({
    email: testEmail,
    password: 'secure_password_123',
  });
  assert.equal(loginRes.status, 200);
  assert.ok(loginRes.body.token);
  assert.equal(loginRes.body.user.email, testEmail);
});
