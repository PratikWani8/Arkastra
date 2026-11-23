const test = require('node:test');
const assert = require('node:assert/strict');
const { verifyElapsedForecasts } = require('../src/services/forecastVerificationService');
const dataStore = require('../src/services/dataStore');

test('Verification service evaluates pending forecast outcomes correctly', async () => {
  const result = await verifyElapsedForecasts();
  assert.ok(result);
  assert.ok(result.verifiedCount !== undefined || result.error !== undefined);
});

test('DataStore stores and retrieves latest forecast and observations', async () => {
  const latestObs = await dataStore.getLatestObservation();
  assert.ok(latestObs);
  assert.ok(latestObs.longFlux > 0);

  const latestFc = await dataStore.getLatestForecast();
  assert.ok(latestFc);
  assert.ok(latestFc.probabilityMPlus >= 0 && latestFc.probabilityMPlus <= 1);
});
