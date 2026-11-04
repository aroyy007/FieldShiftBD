import assert from 'node:assert/strict';
import { test } from 'node:test';
import * as inventoryView from './climate-inventory.ts';

const districts = [
  { code: '1004', name: 'Barguna', name_bn: 'বরগুনা' },
  { code: '3026', name: 'Dhaka', name_bn: 'ঢাকা' },
  { code: '5081', name: 'Rajshahi', name_bn: 'রাজশাহী' },
];

test('cached district choices appear first without hiding districts that lack data', () => {
  assert.equal(typeof inventoryView.buildDistrictOptions, 'function');
  const choices = inventoryView.buildDistrictOptions(districts, {
    cached_count: 1, requires_validation_on_load: true,
    districts: districts.map(item => ({ district_code: item.code, name: item.name,
      name_bn: item.name_bn, status: item.code === '5081' ? 'cached' : 'missing' })),
  }, 'bn');
  assert.deepEqual(choices.map(item => item.value), ['5081', '1004', '3026']);
  assert.equal(choices[0].label, 'রাজশাহী');
  assert.equal(choices[2].label, 'ঢাকা');
});

test('failed or partial inventory retains every canonical district and original selection values', () => {
  assert.equal(typeof inventoryView.buildDistrictOptions, 'function');
  const choices = inventoryView.buildDistrictOptions(districts, null, 'en');
  assert.deepEqual(choices.map(item => item.value), ['1004', '3026', '5081']);
  assert.equal(choices[2].label, 'Rajshahi');
});
