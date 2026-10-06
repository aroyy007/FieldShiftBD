from datetime import date, datetime, timezone
import unittest

from pydantic import ValidationError

from app.services.farm_state import (
    get_task_schedule_state,
    get_season_progress,
    schedule_task_due_at,
)
from app.schemas.farm_state import PlanTaskImportRequest


class TaskScheduleStateTests(unittest.TestCase):
    def test_pending_task_due_today_is_due(self):
        due_at = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
        as_of = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)

        self.assertEqual(get_task_schedule_state("pending", due_at, as_of), "due")

    def test_pending_task_due_before_today_is_overdue(self):
        due_at = datetime(2026, 10, 5, 17, tzinfo=timezone.utc)
        as_of = datetime(2026, 10, 6, 2, tzinfo=timezone.utc)

        self.assertEqual(
            get_task_schedule_state("pending", due_at, as_of), "overdue"
        )

    def test_pending_task_past_deadline_is_overdue_even_on_same_day(self):
        due_at = datetime(2026, 10, 6, 6, tzinfo=timezone.utc)
        as_of = datetime(2026, 10, 6, 6, 1, tzinfo=timezone.utc)

        self.assertEqual(
            get_task_schedule_state("pending", due_at, as_of), "overdue"
        )

    def test_terminal_task_status_is_not_replaced_by_due_state(self):
        due_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
        as_of = datetime(2026, 10, 6, tzinfo=timezone.utc)

        self.assertEqual(
            get_task_schedule_state("completed", due_at, as_of), "completed"
        )

    def test_task_without_due_date_is_unscheduled(self):
        self.assertEqual(
            get_task_schedule_state("pending", None, datetime.now(timezone.utc)),
            "unscheduled",
        )


class SeasonProgressTests(unittest.TestCase):
    def test_progress_is_calculated_and_clamped_to_season_dates(self):
        planting_date = date(2026, 10, 1)
        harvest_date = date(2026, 10, 11)

        self.assertEqual(
            get_season_progress(planting_date, harvest_date, date(2026, 10, 6)), 50
        )
        self.assertEqual(
            get_season_progress(planting_date, harvest_date, date(2026, 9, 30)), 0
        )
        self.assertEqual(
            get_season_progress(planting_date, harvest_date, date(2026, 10, 20)), 100
        )

    def test_progress_is_unknown_without_both_dates(self):
        self.assertIsNone(get_season_progress(None, date(2026, 10, 11), date.today()))


class PlanTaskSchedulingTests(unittest.TestCase):
    def test_due_day_ends_at_midnight_in_bangladesh_and_is_returned_as_utc(self):
        due_at = schedule_task_due_at(date(2026, 10, 1), days_after_planting=3)

        self.assertEqual(
            due_at, datetime(2026, 10, 4, 17, 59, 59, 999999, tzinfo=timezone.utc)
        )

    def test_negative_offset_is_rejected(self):
        with self.assertRaises(ValueError):
            schedule_task_due_at(date(2026, 10, 1), days_after_planting=-1)

    def test_plan_task_references_must_be_unique_within_an_import(self):
        with self.assertRaises(ValidationError):
            PlanTaskImportRequest(
                tasks=[
                    {
                        "reference": "fertilize-1",
                        "growth_stage_id": "00000000-0000-0000-0000-000000000001",
                        "title": "Apply fertilizer",
                        "days_after_planting": 10,
                    },
                    {
                        "reference": "fertilize-1",
                        "growth_stage_id": "00000000-0000-0000-0000-000000000001",
                        "title": "Repeat fertilizer",
                        "days_after_planting": 20,
                    },
                ]
            )

    def test_plan_task_rejects_negative_day_offset(self):
        with self.assertRaises(ValidationError):
            PlanTaskImportRequest(
                tasks=[
                    {
                        "reference": "fertilize-1",
                        "growth_stage_id": "00000000-0000-0000-0000-000000000001",
                        "title": "Apply fertilizer",
                        "days_after_planting": -1,
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
