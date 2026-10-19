"""Evidence binding must not certify stale, partial, or predicted runs."""
import copy,json,pathlib,tempfile,unittest
import balance_pipeline as core


class CalibrationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe=core.read_json(core.DEFAULT_RECIPE);cls.recipe.pop('calibrationEvidence',None)
        cls.plan=core.generate(cls.recipe,'D04');p=cls.plan['tables']['tblevelrating'][0]
        counts=[w['count'] for w in cls.plan['waves'] if w['levelId']==1]
        waves=[{'ordinal':w,'expected':counts[w-1],'successfulSpawned':counts[w-1],'killed':counts[w-1],'leaked':0,
                'combatStartSeconds':(w-1)*15.,'combatEndSeconds':w*15.,'levelEndSeconds':w*15.+(w-1)*5.,
                'gold':30,'hp':20,'peakAlive':4} for w in range(1,p['expectedWaveCount']+1)]
        cls.record={'levelId':1,'profileId':'D04','stars':5,'valid':True,'victory':True,'fiveStarConditions':True,
            'state':'finished','operations':[{'kind':'build','waveOrdinal':1,'combatTimeMs':0}],
            'coverage':'Unity PlayMode test fixture','strategy':'fixture','profile':copy.deepcopy(p),
            'metrics':{k:p[k] for k in ['profileId','profileRevision','balanceRevision','ratingRevision','planHash']}}
        cls.record['metrics'].update(runId='fixture',expectedWaveCount=len(counts),completedWaveCount=len(counts),expectedEnemyCount=sum(counts),
            successfulSpawned=sum(counts),killed=sum(counts),leaked=0,victory=True,statisticsValid=True,timingValid=True,debugOverride=False,
            combatElapsedSeconds=waves[-1]['combatEndSeconds'],levelElapsedSeconds=waves[-1]['levelEndSeconds'],waves=waves)

    def bound(self,record):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'actual.json';p.write_text(json.dumps([record]),encoding='utf-8')
            recipe=copy.deepcopy(self.recipe);recipe['calibrationEvidence']=[str(p)]
            return core.generate(recipe,'D04')

    def test_matching_csharp_decision_binds_complete_wave_inventory_without_hash_change(self):
        plan=self.bound(self.record)
        self.assertEqual(plan['tables']['tblevelrating'][0]['calibrationStatus'],'verified_unity_reference')
        self.assertEqual(plan['tables']['tblevelrating'][0]['planHash'],self.plan['tables']['tblevelrating'][0]['planHash'])
        count=self.plan['wavesPerLevel']
        self.assertEqual([w['unityKilled'] for w in plan['waves'][:count]],[w['count'] for w in self.plan['waves'][:count]])
        self.assertEqual(plan['calibrationEvidence']['verifiedLevelIds'],[1])
        self.assertEqual(len(plan['calibrationEvidence']['pendingLevelIds']),self.plan['levelCount']-1)

    def test_old_20_wave_snapshot_cannot_certify_new_campaign(self):
        record=copy.deepcopy(self.record);record['metrics']['waves']=record['metrics']['waves'][:20]
        record['metrics'].update(expectedWaveCount=20,completedWaveCount=20)
        self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_stale_hash_is_not_certified(self):
        record=copy.deepcopy(self.record);record['metrics']['planHash']='stale'
        plan=self.bound(record);self.assertEqual(plan['calibrationEvidence']['verifiedLevelIds'],[])

    def test_measured_par_is_bound_to_combat_inputs_and_invalidates_on_tower_edit(self):
        recipe=copy.deepcopy(self.recipe);level=self.plan['levels'][0]
        original=self.plan['tables']['tblevelrating'][0]['parCombatTimeMs']
        recipe['parCalibration']={'D04':{'1':{'combatBasisHash':level['combatBasisHash'],
            'parCombatTimeMs':original+5000,'method':'explicit timing witness fixture'}}}
        bound=core.generate(recipe,'D04')
        self.assertTrue(bound['levels'][0]['parCalibrationCurrent'])
        self.assertEqual(bound['tables']['tblevelrating'][0]['parCombatTimeMs'],original+5000)
        recipe['towerValues'][0]['power']+=1
        changed=core.generate(recipe,'D04')
        self.assertFalse(changed['levels'][0]['parCalibrationCurrent'])
        self.assertNotEqual(changed['tables']['tblevelrating'][0]['planHash'],bound['tables']['tblevelrating'][0]['planHash'])

    def test_partial_wave_inventory_is_not_certified(self):
        record=copy.deepcopy(self.record);record['metrics']['waves'][-1]['killed']-=1
        self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_prediction_is_not_unity_evidence(self):
        record=copy.deepcopy(self.record);record['coverage']='offline_prediction_only'
        self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_invalid_csharp_score_is_not_certified(self):
        record=copy.deepcopy(self.record);record['valid']=False
        self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_unfinished_or_failed_operation_trajectory_is_not_certified(self):
        for patch in [{'state':'operation_incomplete'},{'pendingOperations':[{'kind':'build'}]},
                      {'operationError':'build failed'},{'exception':'injected'},{'operations':[]}]:
            with self.subTest(patch=patch):
                record=copy.deepcopy(self.record);record.update(patch)
                self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_self_consistent_stale_wave_inventory_is_not_certified(self):
        record=copy.deepcopy(self.record)
        for key in ['expected','successfulSpawned','killed']:
            record['metrics']['waves'][0][key]+=1
            record['metrics']['waves'][1][key]-=1
        self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_invalid_or_backward_wave_times_are_not_certified(self):
        for patch in [{'combatStartSeconds':float('nan')},{'combatEndSeconds':-1.},
                      {'combatStartSeconds':-1.},{'levelEndSeconds':0.}]:
            with self.subTest(patch=patch):
                record=copy.deepcopy(self.record);record['metrics']['waves'][1].update(patch)
                self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_run_endpoints_must_match_last_wave(self):
        for key in ['combatElapsedSeconds','levelElapsedSeconds']:
            with self.subTest(key=key):
                record=copy.deepcopy(self.record);record['metrics'][key]+=1
                self.assertEqual(self.bound(record)['calibrationEvidence']['verifiedLevelIds'],[])

    def test_millisecond_conversion_matches_csharp_midpoint_rounding(self):
        self.assertEqual(core.seconds_to_ms(632.199999999),632200)
        self.assertEqual(core.seconds_to_ms(.0005),1)
        self.assertEqual(core.seconds_to_ms(-.0005),-1)
        with self.assertRaises(ValueError):core.seconds_to_ms(float('nan'))


if __name__=='__main__':unittest.main(verbosity=2)
