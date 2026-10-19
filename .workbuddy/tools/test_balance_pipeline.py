"""Regression checks for the authoritative compiler; never applies production changes."""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import balance_pipeline as core


class BalanceCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = core.read_json(core.DEFAULT_RECIPE)
        cls.plan = core.generate(cls.recipe, 'D04')

    def wave(self, level, wave, plan=None):
        return next(w for w in (plan or self.plan)['waves'] if w['levelId'] == level and w['waveOrdinal'] == wave)

    def test_preview_compares_float_schema_at_runtime_precision(self):
        self.assertTrue(core.same_runtime_value('tbenemydata','hp',42.322582,42.32258064516129))
        self.assertFalse(core.same_runtime_value('tbenemydata','hp',42.322582,42.323))
        self.assertFalse(core.same_runtime_value('tbsceneinfo','initialGold',100000000,100000001))
        tables=copy.deepcopy(self.plan['tables'])
        tables['tbenemydata'][132]['hp']=float(__import__('struct').unpack('!f',__import__('struct').pack('!f',tables['tbenemydata'][132]['hp']))[0])
        for row in tables['tblevelrating']:row['runtimeContentHash']='derived-applied-hash'
        original=core.read_json
        def read(path,default=None):
            p=pathlib.Path(path)
            return copy.deepcopy(tables[p.stem]) if p.parent.name=='ConfigJson' and p.stem in tables else original(path,default)
        with mock.patch.object(core,'read_json',side_effect=read):
            self.assertEqual(core.preview(self.plan)['changes'],[])

    def test_reference_counts_budgets_and_par(self):
        levels,waves,_=core.dimensions(self.recipe)
        self.assertEqual((levels,waves), (30,25))
        self.assertEqual(len(self.plan['waves']), levels*waves)
        f=self.recipe['formula']
        for level in range(1, levels+1):
            seq = [self.wave(level, wave) for wave in range(1, waves+1)]
            self.assertEqual([w['count'] for w in seq], [level*f['countLevelCoefficient']+w*f['countWaveCoefficient']+f['countOffset'] for w in range(1,waves+1)])
            self.assertTrue(all(a['actualEhp'] < b['actualEhp'] for a,b in zip(seq,seq[1:])))
        ratings = self.plan['tables']['tblevelrating']
        self.assertEqual(len(ratings),levels)
        self.assertTrue(all(r['expectedWaveCount']==waves and r['parCombatTimeMs']>0 for r in ratings))

    def test_final_lists_not_descriptions_are_validated(self):
        altered = copy.deepcopy(self.plan)
        altered['tables']['tbenemylist'][0]['EnemyIndexs'].pop()
        report = core.validate(altered)
        self.assertFalse(report['passed'])
        self.assertTrue(any('count' in message for message in report['errors']))

    def test_generate_does_not_mutate_recipe_or_production(self):
        before = core.source_hashes()
        frozen = core.canonical(self.recipe)
        core.generate(self.recipe, 'D08')
        self.assertEqual(core.canonical(self.recipe), frozen)
        self.assertEqual(core.source_hashes(), before)

    def test_round_trip_profile_switch_keeps_d04_identity(self):
        first = self.plan
        other = core.generate(self.recipe, 'D08')
        again = core.generate(self.recipe, 'D04', other['manifest'])
        self.assertEqual(first['tables'], again['tables'])
        self.assertEqual(first['waves'], again['waves'])

    def test_same_priority_overlap_is_error(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['overrides'] = [dict(id=name, target='wave', scope='wave', levelId=1,
                                    waveOrdinal=1, field='targetEhp', mode='multiply', value=1.1)
                               for name in ['edit-a', 'edit-b']]
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            core.generate(recipe, 'D04')

    def test_precedence_global_level_range_then_wave(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['overrides'] = [dict(id='global', target='wave', scope='global', field='targetEhp', mode='multiply', value=1.1),
            dict(id='level', target='wave', scope='level', levelId=1, field='targetEhp', mode='multiply', value=1.1),
            dict(id='range', target='wave', scope='range', levelId=1, waveStart=1, waveEnd=2, field='targetEhp', mode='multiply', value=1.1),
            dict(id='wave', target='wave', scope='wave', levelId=1, waveOrdinal=1, field='targetEhp', mode='replace', value=300)]
        plan = core.generate(recipe, 'D04')
        self.assertAlmostEqual(self.wave(1, 1, plan)['actualEhp'], 300, places=3)

    def test_illegal_quantity_is_reported_instead_of_silently_repaired(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['overrides'] = [dict(id='count-conflict', target='wave', scope='wave', levelId=1,
                                    waveOrdinal=2, field='count', mode='replace', value=8)]
        plan = core.generate(recipe, 'D04')
        self.assertEqual(self.wave(1, 2, plan)['count'], 8)
        self.assertFalse(core.validate(plan)['passed'])

    def test_integer_field_rejects_fraction(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['overrides'] = [dict(id='fraction', target='wave', scope='wave', levelId=1,
                                    waveOrdinal=1, field='count', mode='replace', value=8.5)]
        with self.assertRaises(ValueError):
            core.generate(recipe, 'D04')

    def test_changed_tower_changes_every_affected_rating_key(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['towerValues'][0]['power'] += 1
        plan = core.generate(recipe, 'D04')
        for a, b in zip(self.plan['tables']['tblevelrating'], plan['tables']['tblevelrating']):
            self.assertNotEqual(a['planHash'], b['planHash'])
            self.assertEqual(b['calibrationStatus'], 'pending_unity_reference')

    def test_blocked_map_fails_bfs(self):
        self.assertFalse(core.path_for(['S#E']))
        self.assertTrue(core.path_for(['S.E']))

    def test_every_profile_baseline_gradient_is_exact(self):
        base_ehp=self.wave(1,1)['actualEhp']
        for i, profile in enumerate(self.recipe['profiles'][:8]):
            plan = core.generate(self.recipe, profile['id'])
            self.assertEqual(plan['tables']['tbsceneinfo'][0]['initialGold'], core.round_up(self.recipe['formula']['initialGold']*profile['goldMultiplier']))
            self.assertAlmostEqual(self.wave(1, 1, plan)['actualEhp'], base_ehp*profile['ehpMultiplier'], delta=.01)
            self.assertTrue(core.validate(plan)['passed'])

    def test_capacity_minimizes_buildable_cost_instead_of_steps(self):
        from balance_campaign import capacity
        audit=capacity(['SPPPE','.....'])
        self.assertEqual(audit['reservedBuildableCells'],0)
        self.assertEqual(audit['capacity'],5)
        with self.assertRaises(ValueError):capacity(['S#E'])

    def test_runtime_tie_order_matches_shipped_unity_path_probe(self):
        from balance_campaign import runtime_path_for
        self.assertEqual(runtime_path_for(['S..','..E']),[(0,0),(0,1),(1,1),(2,1)])
        self.assertEqual(runtime_path_for(['S#E']),[])
        for board in self.plan['tables']['tblevelmap']:
            self.assertEqual(len(runtime_path_for(board['cells'])),len(core.path_for(board['cells'])))

    def test_legacy_ids_and_new_ids_remain_globally_unique(self):
        from balance_campaign import prepare_manifest
        manifest=self.plan['manifest']
        for category in ['rounds','enemyLists','variants']:
            ids=list(manifest[category].values());self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(manifest['rounds']['20|20'],400)
        self.assertGreater(manifest['rounds']['1|21'],400)
        self.assertEqual(len(self.plan['tables']['tbenemydata'][:132]),132)

    def test_blast_radius_invalidates_rating_identity(self):
        recipe=copy.deepcopy(self.recipe);recipe['bulletValues'][0]['aoeRadius']+=.1
        changed=core.generate(recipe,'D04')
        self.assertNotEqual(changed['tables']['tblevelrating'][0]['planHash'],self.plan['tables']['tblevelrating'][0]['planHash'])

    def test_no_early_giant_or_boss(self):
        for w in self.plan['waves']:
            if w['levelId'] < 12:
                self.assertEqual(w['bossCount'], 0)
            if w['levelId'] == 1:
                self.assertTrue(all(c['canonicalEnemyId'] not in (67, 70, 129, 130, 131, 132) for c in w['composition']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
