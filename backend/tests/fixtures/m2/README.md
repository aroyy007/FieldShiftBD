# M2 synthetic test fixtures

**TEST ONLY — SYNTHETIC MOCK DATA — NOT AGRICULTURAL ADVICE.**

`synthetic_golden_farm.json` exercises the existing M1 → M2 and M2 → M3
contracts. All farmer, farm, crop, evidence, stage, task-definition, and harvest
values are invented for tests. The synthetic evidence rows use an `approved`
review status only to exercise the approved-evidence code path in an isolated
test database; that status is not an agronomic review or endorsement.

Never copy this fixture into production seeds, migrations, or a real farm
workflow. Tests load it only into a temporary SQLite database.
