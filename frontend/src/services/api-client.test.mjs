import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { apiRequest, setApiAccessTokenProvider } from './api-client.ts';
import { mapFarmlandData, normalizeBangladeshPhone } from './farm-data.ts';

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  setApiAccessTokenProvider(async () => null);
});

test('apiRequest sends JSON with the active farmer token', async () => {
  let request;
  globalThis.fetch = async (url, init) => {
    request = { url, init };
    return new Response(JSON.stringify({ id: 'farm-1' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  setApiAccessTokenProvider(async () => 'farmer-token');

  const response = await apiRequest('/farmlands', {
    method: 'POST',
    body: { name: 'North Field' },
  });

  assert.deepEqual(response, { id: 'farm-1' });
  assert.equal(request.url, 'http://127.0.0.1:8000/farmlands');
  assert.equal(request.init.headers.get('Authorization'), 'Bearer farmer-token');
  assert.equal(request.init.headers.get('Content-Type'), 'application/json');
  assert.equal(request.init.body, JSON.stringify({ name: 'North Field' }));
});

test('apiRequest preserves backend validation errors and status codes', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Farmland not found' }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' },
  });

  await assert.rejects(
    apiRequest('/farmlands/missing'),
    error => error.status === 404 && error.message === 'Farmland not found',
  );
});

test('apiRequest reports backend connectivity failures clearly', async () => {
  globalThis.fetch = async () => { throw new TypeError('fetch failed'); };

  await assert.rejects(
    apiRequest('/profile'),
    /Could not connect to the backend/,
  );
});

test('apiRequest leaves multipart boundaries to fetch for image uploads', async () => {
  let request;
  globalThis.fetch = async (_url, init) => {
    request = init;
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  };
  const form = new FormData();
  form.append('image', new Blob(['photo'], { type: 'image/jpeg' }), 'photo.jpg');

  await apiRequest('/farmlands/farm-1/disease-results', { method: 'POST', body: form });

  assert.equal(request.headers.has('Content-Type'), false);
  assert.equal(request.body, form);
});

test('Bangladesh phone numbers are normalized to E.164', () => {
  assert.equal(normalizeBangladeshPhone('01712-345678'), '+8801712345678');
  assert.equal(normalizeBangladeshPhone('+880 1712 345678'), '+8801712345678');
  assert.equal(normalizeBangladeshPhone('8801712345678'), '+8801712345678');
});

test('farmland mapping uses persisted M1, M3, and M6-compatible values only', () => {
  const farm = mapFarmlandData({
    id: 'farm-1', name: 'North Field', division: 'Dhaka', district: 'Gazipur',
    upazila: null, village_or_locality: null, land_area_sqm: '8093.7128448',
    land_area_display_unit: 'acre', soil_type: 'Clay loam',
    irrigation_available: true, water_source: 'Tube well',
  }, {
    active_season: { id: 'season-1', crop_name: 'Aman Rice', planting_date: '2026-07-01', expected_harvest_date: '2026-11-01' },
    current_growth_stage: { id: 'stage-2', name: 'Vegetative', sequence: 2, start_day: 12, end_day: 34 },
    growth_stages: [
      { id: 'stage-1', name: 'Seedling', sequence: 1, start_day: 0, end_day: 11 },
      { id: 'stage-2', name: 'Vegetative', sequence: 2, start_day: 12, end_day: 34 },
    ],
    season_progress_percent: 25,
    days_since_planting: 20,
  }, [{
    id: 'task-1', title: 'Inspect field', description: null, status: 'pending',
    due_at: null, priority: 'normal', source: 'farmer', growth_stage_id: 'stage-2',
  }], [{
    id: 'problem-1', category: 'Pest', description: 'Check leaves', source: 'farmer',
    severity: 'moderate', status: 'open', created_at: '2026-10-07T00:00:00Z', resolved_at: null,
  }], [{
    id: 'checkin-1', checkin_at: '2026-10-07T00:00:00Z', growth_stage_id: 'stage-2',
    notes: 'Healthy', observations: { water_condition: 'Balanced' },
  }]);

  assert.equal(farm.id, 'farm-1');
  assert.equal(farm.crop, 'Aman Rice');
  assert.equal(farm.acreage, 2);
  assert.equal(farm.growthStage, 'Vegetative');
  assert.equal(farm.tasks[0].id, 'task-1');
  assert.equal(farm.problems[0].id, 'problem-1');
  assert.equal(farm.checkIns[0].observations.waterCondition, 'Balanced');
  assert.equal(farm.seasonPlan[0].status, 'completed');
  assert.equal(farm.seasonPlan[1].status, 'current');
  assert.equal(farm.alerts.length, 0);
});
