"""Match published references by cultivar, season and exact establishment method."""
import json
import re
from pathlib import Path
from app.services.crop_calendar_references import published_calendar_references

EXTENSIONS = Path(__file__).resolve().parents[2] / 'data/m2_knowledge_sources/rotation_calendar_extensions.json'


def _key(value):
    return re.sub(r'[^a-z0-9]', '', value.casefold())


def calendar_references() -> list[dict]:
    references = []
    for r in published_calendar_references('rice'):
        references.append({'profile_id':r.profile_id,'crop_code':'rice','variety_name':r.variety_name,
            'variety_name_bn':r.variety_name_bn,'season_code':r.season.casefold(),
            'cultivation_method':r.cultivation_method,'establishment_window':r.transplanting_window.model_dump(),
            'harvest_window':r.harvest_window.model_dump(),'source_url':r.source_url,
            'source_id':r.profile_id,'accessed_on':str(r.source_accessed),
            'scope_en':r.geographic_scope_en,'scope_bn':r.geographic_scope_bn})
    references.extend(json.loads(EXTENSIONS.read_text())['profiles'])
    return references


def match_calendar_references(step: dict) -> dict:
    varieties = {_key(n) for n in step.get('variety_names', [])}
    candidates = [r for r in calendar_references() if r['crop_code'] == step['crop_code']
                  and r['season_code'] == step.get('season_code') and _key(r['variety_name']) in varieties]
    if not candidates:
        return {'status':'not_available','matching':[],'available':[]}
    method = step.get('cultivation_method', 'unspecified')
    if method == 'unspecified':
        return {'status':'method_not_recorded','matching':[],'available':candidates}
    matching = [r for r in candidates if r['cultivation_method'] == method]
    return {'status':'source_reference_available' if matching else 'method_mismatch',
            'matching':matching,'available':candidates}



def build_calendar_evidence(step: dict, planning_year: int, bundle=None):
    from app.contracts.challenge.v2 import CalendarStepEvidenceV2, CalendarReferenceV2
    from src.compute.rotation_exposure import calendar_weather_bounds
    match = match_calendar_references(step)
    matching = {r['profile_id'] for r in match['matching']}
    rows = [r.model_dump() for r in bundle.daily_series] if bundle else []
    references = []
    for item in match['available']:
        fields = {k:v for k,v in item.items() if k not in {'crop_code','season_code'}}
        fields['evidence_ids'] = [item['source_id']]
        if item['profile_id'] in matching and bundle:
            fields['weather'] = calendar_weather_bounds(rows,item['establishment_window'],item['harvest_window'],planning_year=planning_year)
            fields['evidence_ids'].append('power-history')
        references.append(CalendarReferenceV2.model_validate(fields))
    return CalendarStepEvidenceV2(status=match['status'], references=references,
        limitation_en='Published cultivar windows only; no cultivar is selected. Weather is historical calendar-period context, not stage exposure, water demand or planting advice. Agronomy review is pending.',
        limitation_bn='প্রকাশিত জাতের সময়সীমা; কোনো জাত বাছাই করা হয়নি। বৃষ্টি ঐতিহাসিক সময়ের প্রেক্ষাপট, বৃদ্ধির ধাপ, পানির চাহিদা বা রোপণের পরামর্শ নয়। কৃষিবিদের পর্যালোচনা বাকি।')
