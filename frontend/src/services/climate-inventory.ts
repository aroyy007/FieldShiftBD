import type { DistrictCacheEntry, DistrictCacheInventory } from '../modules/shared/contracts.generated';
import type { DistrictRef } from './m1-reference';
import type { PickerOption } from '../components/OptionPickerModal';

export function cacheStatusLabel(status: DistrictCacheEntry['status'] | undefined, language: 'bn' | 'en') {
  const labels = language === 'bn'
    ? { cached: 'সংরক্ষিত তথ্য আছে; খোলার সময় যাচাই হবে', missing: 'ঐতিহাসিক তথ্য এখনও প্রস্তুত নেই', unreadable: 'তথ্য এখন ব্যবহার করা যাচ্ছে না' }
    : { cached: 'Saved data present; validated when opened', missing: 'Historical data not prepared yet', unreadable: 'Data cannot be used right now' };
  return status ? labels[status] : (language === 'bn' ? 'তথ্যের উপস্থিতি যাচাই হয়নি' : 'Data presence not checked');
}

/** Prioritize saved data without removing choices for published calendars. */
export function buildDistrictOptions(
  districts: readonly Pick<DistrictRef, 'code' | 'name' | 'name_bn'>[],
  inventory: DistrictCacheInventory | null,
  language: 'bn' | 'en',
): PickerOption[] {
  const statuses = new Map(inventory?.districts.map(item => [item.district_code, item.status]));
  return [...districts]
    .sort((left, right) => Number(statuses.get(right.code) === 'cached') - Number(statuses.get(left.code) === 'cached'))
    .map(item => ({
      value: item.code,
      label: language === 'bn' ? item.name_bn : item.name,
      detail: `${language === 'bn' ? item.name : item.name_bn} · ${cacheStatusLabel(statuses.get(item.code), language)}`,
    }));
}
