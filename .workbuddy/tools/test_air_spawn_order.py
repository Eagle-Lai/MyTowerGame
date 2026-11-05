"""Contract tests for read-only air-order checks (no project files mutated)."""
import unittest
from decimal import Decimal
from pathlib import Path
import tempfile
from zipfile import ZipFile
from check_air_spawn_order import Record, compare_data, inspect_data, load_data, normalize, read_xlsx


def record(**values):
    return Record(values, {"path": "fixture.xlsx", "sheet": "Sheet", "row": 4,
                           "columns": {"EnemyIndexs": "C"}})


def fixture(groups, rounds=None, order=None):
    rounds = rounds or {1: list(groups)}
    return {"SceneInfo": {1: record(id=1, RoundList=order or list(rounds))},
            "RoundData": {key: record(id=key, EnemyIndexs=ids, interval=0) for key, ids in rounds.items()},
            "EnemyList": {key: record(id=key, EnemyIndexs=ids, interval=0, enemyInterval=Decimal(252))
                          for key, ids in groups.items()},
            "EnemyData": {1: record(id=1, isFlying=0, name="other"),
                          2: record(id=2, isFlying=1, name="Bat"),
                          3: record(id=3, isFlying=1, name="Eye")}}


class AirSpawnOrderTests(unittest.TestCase):
    def test_separated_air_passes(self):
        report = inspect_data(fixture({1: [2, 1, 3, 1, 2]}), [1])
        self.assertEqual((report["pairCount"], report["airCount"], report["errors"]), (0, 3, []))

    def test_same_and_different_air_ids_are_both_violations(self):
        report = inspect_data(fixture({1: [2, 2, 3]}), [1])
        self.assertEqual(report["pairCount"], 2)
        self.assertEqual([(p["first"]["enemyId"], p["second"]["enemyId"]) for p in report["pairs"]],
                         [(2, 2), (2, 3)])

    def test_adjacent_groups_are_checked(self):
        report = inspect_data(fixture({1: [1, 2], 2: [3, 1]}), [1])
        self.assertEqual(report["pairs"][0]["boundary"], "group")
        self.assertEqual(report["pairs"][0]["gapMs"], 252)

    def test_round_order_comes_from_scene_not_id_sort(self):
        data = fixture({1: [1, 2], 2: [3, 1]}, {20: [1], 10: [2]}, [20, 10])
        report = inspect_data(data, [1])
        self.assertEqual(report["pairs"][0]["boundary"], "round")
        self.assertEqual(report["pairs"][0]["second"]["roundId"], 10)

    def test_missing_enemy_is_error_and_does_not_create_fake_pair(self):
        report = inspect_data(fixture({1: [2, 999, 3]}), [1])
        self.assertEqual(report["pairCount"], 0)
        self.assertIn("missing enemyId=999", report["errors"][0])

    def test_missing_group_and_round_fail(self):
        data = fixture({1: [1, 2]})
        data["RoundData"][1].values["EnemyIndexs"].append(999)
        data["SceneInfo"][1].values["RoundList"].append(888)
        report = inspect_data(data, [1])
        self.assertEqual(len(report["errors"]), 2)

    def test_nonzero_flying_flag_is_air_even_with_unrelated_name(self):
        data = fixture({1: [2, 3]})
        data["EnemyData"][2].values.update(isFlying=2, name="QuickEnemy")
        report = inspect_data(data, [1])
        self.assertEqual(report["pairCount"], 1)

    def test_repeated_group_reference_is_not_silently_accepted(self):
        report = inspect_data(fixture({1: [1, 2]}, {1: [1, 1]}), [1])
        self.assertTrue(any("repeated group" in e for e in report["errors"]))

    def test_stale_export_fails_even_when_both_have_no_adjacent_air(self):
        first, second = fixture({1: [2, 1, 3]}), fixture({1: [3, 1, 2]})
        self.assertEqual(inspect_data(first, [1])["pairCount"], 0)
        self.assertEqual(inspect_data(second, [1])["pairCount"], 0)
        self.assertIn("EnemyList id=1 field=EnemyIndexs", compare_data(first, second, [1])[0])

    def test_unrelated_enemy_interval_does_not_affect_air_flag_parsing(self):
        enemy = normalize(record(id="2", isFlying="1", interval="100"), "EnemyData")
        self.assertEqual(enemy.values["isFlying"], 1)

    def test_empty_inline_cell_and_list_addresses_in_source_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.xlsx"
            with ZipFile(path, "w") as archive:
                archive.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
                archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="/xl/worksheets/sheet1.xml"/></Relationships>')
                archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="B1" t="inlineStr"><is><t>id</t></is></c><c r="C1" t="inlineStr"><is><t>EnemyIndexs</t></is></c><c r="D1" t="inlineStr"><is><t>interval</t></is></c><c r="E1" t="inlineStr"><is><t>enemyInterval</t></is></c><c r="F1" t="inlineStr"><is><t>desc</t></is></c></row><row r="4"><c r="B4"><v>8</v></c><c r="C4" t="inlineStr"><is><t>2,1,3</t></is></c><c r="D4"><v>0</v></c><c r="E4"><v>252</v></c><c r="F4" t="inlineStr"/></row></sheetData></worksheet>')
            rows = list(read_xlsx(path))
            group = normalize(rows[0], "EnemyList")
            self.assertEqual(group.values["EnemyIndexs"], [2, 1, 3])
            self.assertEqual(group.source["columns"]["EnemyIndexs"], "C")
            self.assertEqual(group.source["row"], 4)

    def test_missing_input_is_never_a_valid_empty_result(self):
        with tempfile.TemporaryDirectory() as directory:
            _, errors = load_data(Path(directory), "json")
            self.assertTrue(any("tbsceneinfo.json" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
