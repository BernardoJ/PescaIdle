"""Controls of the comparator; mutates only synthetic recorded results."""
import argparse,copy,json,os,subprocess,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import comparar_fluxo_base as comparator

class ComparatorControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=comparator.read(comparator.FIXTURES)
        cls.fsha=comparator.digest(comparator.FIXTURES.read_bytes())
        cls.left=comparator.read(RUN/'work/candidate.json')
        cls.right=comparator.read(RUN/'work/candidate_self.json')
        cls.observed=[]

    def cli(self,label,left,right,expected):
        paths=[]
        for side,record in (('left',left),('right',right)):
            p=OUT/(label+'-'+side+'.json');comparator.dump(p,record);paths.append(p)
        cmd=[sys.executable,'-X','utf8','-B',str(Path(comparator.__file__)),
             '--compare-records',str(paths[0]),str(paths[1]),'--out',str(OUT/(label+'-result'))]
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=90)
        self.observed.append({'case':label,'expected':expected,'observed':p.returncode})
        self.assertEqual(p.returncode,expected,p.stdout+p.stderr)
        return comparator.read(OUT/(label+'-result')/('erro.json' if expected==2 else 'resultado.json'))

    def test_01_independent_same_revision_positive_cli(self):
        result=self.cli('positive-self',self.left,self.right,0)
        self.assertTrue(result['equivalent']);self.assertIsNone(result['first_difference'])

    def test_02_species_negative_cli(self):
        bad=copy.deepcopy(self.left);bad['scenarios'][0]['timeline'][0]['events'][0]['species_id']='synthetic_species'
        result=self.cli('negative-species',self.left,bad,1)
        self.assertIn('species_id',result['first_difference']['path'])

    def test_03_balance_negative_cli(self):
        bad=copy.deepcopy(self.left);bad['scenarios'][0]['timeline'][0]['state']['moedas_centavos']+=1
        result=self.cli('negative-balance',self.left,bad,1)
        self.assertIn('moedas_centavos',result['first_difference']['path'])

    def test_04_order_negative_cli(self):
        bad=copy.deepcopy(self.left);events=bad['scenarios'][0]['timeline'][0]['events'];events[0],events[1]=events[1],events[0]
        result=self.cli('negative-order',self.left,bad,1)
        self.assertIn('events[0]',result['first_difference']['path'])

    def test_05_incomplete_both_must_error_cli(self):
        bad=copy.deepcopy(self.left);bad['scenarios'].pop()
        self.cli('incomplete',bad,bad,2)

    def test_06_incomplete_timeline_both_must_error(self):
        bad=copy.deepcopy(self.left);case=next(c for c in bad['scenarios'] if c['kind']=='progression');case['timeline'].pop()
        with self.assertRaises(ValueError):comparator.compare_runs(bad,bad,self.fixture,self.fsha)

    def test_07_no_silent_unknown_metadata(self):
        e=copy.deepcopy(next(e for c in self.left['scenarios'] for f in c['timeline'] for e in f['events'] if 'measurement' in e))
        e['unapproved_bonus']=10
        clean=comparator.normalize_event(e,comparator.stats_empty())
        self.assertEqual(clean['unapproved_bonus'],10)
        e['measurement']['gain_cents']=10
        clean=comparator.normalize_event(e,comparator.stats_empty());self.assertIn('measurement',clean)

    def test_08_event_length_and_type_strict(self):
        self.assertEqual(comparator.first_difference([1],[1,2])['reason'],'length')
        self.assertEqual(comparator.first_difference(1,True)['reason'],'type')

    def test_09_additions_are_classified(self):
        run=comparator.read(RUN/'resultado.json')
        self.assertGreater(sum(c['candidate_additions']['measured_events'] for c in run['scenarios']),0)
        self.assertGreater(sum(c['candidate_additions']['size_award_notifications'] for c in run['scenarios']),0)
        self.assertEqual(sum(c['candidate_additions']['migration_backups'] for c in run['scenarios']),2)

    def test_10_price_and_time_not_normalized(self):
        a=self.left['scenarios'][0];b=copy.deepcopy(a)
        b['timeline'][0]['events'][0]['context']['utc']+=.001
        x,_=comparator.normalize_scenario(a);y,_=comparator.normalize_scenario(b)
        self.assertIn('context.utc',comparator.first_difference(x,y)['path'])
        catalogue=copy.deepcopy(self.left['catalogue']);catalogue['shop'][2][3]+=1
        self.assertIsNotNone(comparator.first_difference(self.left['catalogue'],catalogue))

    def test_11_existing_out_not_overwritten(self):
        target=OUT/'existing';target.mkdir();(target/'sentinel').write_text('preserved')
        p=subprocess.run([sys.executable,'-B',str(Path(comparator.__file__)),'--out',str(target),
            '--compare-records',str(RUN/'work/candidate.json'),str(RUN/'work/candidate_self.json')],capture_output=True,timeout=15)
        self.assertEqual(p.returncode,2);self.assertEqual([f.name for f in target.iterdir()],['sentinel'])

    def test_12_bad_config_cli_returns_2(self):
        p=subprocess.run([sys.executable,'-B',str(Path(comparator.__file__)),'--out',str(OUT/'bad-sha'),
                          '--candidate','HEAD'],capture_output=True,timeout=15)
        self.assertEqual(p.returncode,2);self.assertFalse((OUT/'bad-sha/work').exists())

    def test_13_empty_matrix_cannot_be_equivalence(self):
        fixture={'version':1,'cases':[]}
        run={'format':1,'complete':True,'fixture_sha256':'test','scenarios':[],'historical_projection':[]}
        with self.assertRaises(ValueError):comparator.validate_run(run,fixture,'test')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args();RUN=args.run_dir.resolve();OUT=args.out.resolve()
    try:
        for name in ('candidate.json','candidate_self.json'):
            if not (RUN/'work'/name).is_file():raise ValueError('Run directory is missing completed worker records')
        OUT.mkdir(parents=True,exist_ok=False)
    except (OSError,ValueError) as exc:
        print(str(exc),file=sys.stderr);sys.exit(2)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ComparatorControls))
    comparator.dump(OUT/'testes.json',{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                                    'cli_controls':ComparatorControls.observed})
    sys.exit(0 if result.wasSuccessful() else 1)
