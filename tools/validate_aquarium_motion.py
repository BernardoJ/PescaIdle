"""Focused visual checks, timing and evidence. Synthetic memory only, no fishing/save."""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from tools.aquarium_preview import isolate, synthetic_state

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--benchmark-only',action='store_true')
    args=parser.parse_args()
    root=args.source.resolve(strict=True);out=isolate(args.out,root)
    from PIL import Image
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import Qt, QRectF
    from PySide6.QtGui import QImage, QPainter, QColor, QFont
    from PySide6.QtWidgets import QApplication, QWidget
    from pesca_catalogo import ESPECIES
    from pesca_museu_ui import AquariumView, MuseuDialog
    from pesca_tamanhos import exhibit, RULES
    from pesca_tamanho_visual import scale_for
    from pesca_especies_visual import species_image
    from pesca_museu_visual import aquarium_species_image
    from pesca_ui import configure_app
    app=QApplication([]);app.setQuitOnLastWindowClosed(False);configure_app(app)
    ids=tuple(id_ for id_,s in ESPECIES.items() if s['categoria']=='peixe')
    checks={}
    def pil(image):
        image=image.convertToFormat(QImage.Format_RGBA8888)
        return Image.frombytes('RGBA',(image.width(),image.height()),bytes(image.constBits()))
    def digest(image):return hashlib.sha256(bytes(image.constBits())).hexdigest()
    improved=(root/'assets/aquario_movimento.json').exists()
    if improved:
        from pesca_museu_visual import (ART, MOTION, WAVE, aquarium_species_image,
                                        animation_frame, _paint_species)
    if not args.benchmark_only:
        if not improved:raise ValueError('Full visual checks require the animated candidate.')
        class VisualChecks(unittest.TestCase):
            def test_01_catalogue_and_motion_metadata(self):
                self.assertEqual(set(ids),set(ART['species']))
                self.assertEqual(set(ids),set(MOTION['species']))
                self.assertEqual(68,len(ids));self.assertEqual(8,len(WAVE))
                for id_ in ids:
                    p,m=ART['species'][id_],MOTION['species'][id_]
                    self.assertIn(m['style'],('caudal','undulate','fins'))
                    self.assertGreater(m['step_seconds'],0)
                    for key,layer in [('tail_back','back'),('fins_back','back'),('fins_front','front')]:
                        for i in m[key]:
                            self.assertTrue(0<=i<len(p[layer]))
                            self.assertEqual('poly',p[layer][i][0])
                checks['eligible_species']=len(ids)
            def test_02_rest_frame_matches_steps_1_to_3(self):
                old=json.loads((root/'docs/aquario-especies/evidencias/depois/manifest.json').read_text(encoding='utf-8'))
                for id_ in ids:self.assertEqual(old['sprite_hashes'][id_],digest(aquarium_species_image(id_,2,0)),id_)
                checks['unchanged_rest_masters']=len(ids)
            def test_03_every_species_moves_at_both_details(self):
                variants={}
                for id_ in ids:
                    variants[id_]={}
                    for detail in (1,2):
                        n=len({digest(aquarium_species_image(id_,detail,f)) for f in range(8)})
                        self.assertGreaterEqual(n,2,(id_,detail))
                        variants[id_][str(detail)]=n
                checks['distinct_frames_by_species_and_detail']=variants
            def test_04_unclipped_master_frames(self):
                n=0
                for id_,detail,frame in itertools.product(ids,(1,2),range(8)):
                    padded=QImage(80,56,QImage.Format_ARGB32_Premultiplied)
                    padded.fill(Qt.transparent);p=QPainter(padded);p.translate(4,4)
                    _paint_species(p,id_,detail,frame);p.end()
                    bounds=pil(padded).getbbox()
                    self.assertIsNotNone(bounds)
                    self.assertTrue(bounds[0]>=4 and bounds[1]>=4 and bounds[2]<=76 and bounds[3]<=52,(id_,detail,frame,bounds))
                    n+=1
                checks['unclipped_padded_masters']=n
            def test_05_positions_bounds_and_overlap(self):
                state=synthetic_state();view=AquariumView(lambda:state,ESPECIES)
                n=0;period=2*math.pi/.19
                # Every species occupies every slot; largest available specimen.
                for id_,slot in itertools.product(ids,range(3)):
                    other=[i for i in ('lambari','tilapia_do_nilo','carpa_comum','traira') if i!=id_][:2]
                    selected=other[:];selected.insert(slot,id_);state=synthetic_state(selected)
                    for i in range(600):
                        rects=[]
                        for fish,x,y,reverse in view.fish_positions(i*period/599):
                            s=scale_for(exhibit(state,state['museu']['aquario'].index(fish)),fish)
                            rects.append(QRectF(x-18*s,y-12*s,36*s,24*s))
                        for rect in rects:
                            self.assertGreaterEqual(rect.left(),16-1e-8);self.assertLessEqual(rect.right(),240+1e-8)
                            self.assertGreaterEqual(rect.top(),16-1e-8);self.assertLessEqual(rect.bottom(),106+1e-8)
                        for a,b in itertools.combinations(rects,2):self.assertFalse(a.intersects(b))
                        n+=1
                view.close();checks['three_fish_position_samples']=n
            def test_06_small_large_mixed_and_reverse(self):
                state=synthetic_state();view=AquariumView(lambda:state,ESPECIES);n=0
                for choices in itertools.product(('menor','maior'),repeat=3):
                    state=synthetic_state(choices=list(choices))
                    for phase in (0.,.25,.5,1.,4.,8.,16.,24.,32.):
                        before=copy.deepcopy(state)
                        for detail in (1,2):
                            image=view.render_image(phase,detail)
                            self.assertEqual((256*detail,128*detail),(image.width(),image.height()))
                            self.assertFalse(image.isNull());n+=1
                        self.assertEqual(before,state)
                view.close();checks['mixed_size_tank_renders']=n
            def test_07_clock_and_invalid_inputs(self):
                for id_ in ids:
                    step=MOTION['species'][id_]['step_seconds']
                    self.assertEqual(0,animation_frame(id_,0))
                    for f in range(8):self.assertEqual(f,animation_frame(id_,(f+.1)*step))
                    self.assertEqual(0,animation_frame(id_,8.1*step))
                for frame in (-1,8,True,.5):
                    with self.assertRaises(ValueError):aquarium_species_image('lambari',2,frame)
                with self.assertRaises(ValueError):aquarium_species_image('lambari',3,0)
                with self.assertRaises(ValueError):animation_frame('lambari',float('nan'))
            def test_08_no_state_rng_or_shared_art_mutation(self):
                state=synthetic_state();before=copy.deepcopy(state);rng=random.getstate()
                shared={id_:digest(species_image(id_)) for id_ in ids}
                artwork=copy.deepcopy(ART)
                with patch.object(random.Random,'random',side_effect=AssertionError('RNG consumed')),patch.object(random.Random,'getrandbits',side_effect=AssertionError('RNG consumed')):
                    for frame in range(8):
                        view=AquariumView(lambda:state,ESPECIES)
                        view.render_image(frame*.2,2);view.close()
                    for id_,frame in itertools.product(ids,range(8)):aquarium_species_image(id_,2,frame)
                self.assertEqual(before,state);self.assertEqual(rng,random.getstate());self.assertEqual(artwork,ART)
                self.assertEqual(shared,{id_:digest(species_image(id_)) for id_ in ids})
                checks.update(state_unchanged=True,global_rng_unchanged=True,shared_fishing_art_unchanged=True)
            def test_09_cache_is_bounded_and_reused(self):
                image=aquarium_species_image('lambari',2,2)
                hits=aquarium_species_image.cache_info().hits
                self.assertIs(image,aquarium_species_image('lambari',2,2))
                self.assertGreater(aquarium_species_image.cache_info().hits,hits)
                self.assertLessEqual(aquarium_species_image.cache_info().currsize,512)
            def test_10_timer_lifecycle(self):
                state=synthetic_state();view=AquariumView(lambda:state,ESPECIES)
                view.setAttribute(Qt.WA_DontShowOnScreen,True);view.show();app.processEvents()
                self.assertTrue(view.timer.isActive());view.hide();app.processEvents()
                self.assertFalse(view.timer.isActive());view.show();app.processEvents()
                self.assertTrue(view.timer.isActive());view.close();app.processEvents()
                self.assertFalse(view.timer.isActive())
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(VisualChecks))
        checks['tests']=dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors))
        (out/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
        if not result.wasSuccessful():return 1

    # Isolated renderer microbenchmark: excludes OS compositor, Qt event queue and game.
    timing={}
    scenes={'empty':[None]*3,'pilot':['lambari','tilapia_do_nilo','carpa_comum'],
            'special':['cavalinho_do_mar_pigmeu','peixe_lua','enguia_pelicano']}
    for name,selected in scenes.items():
        state=synthetic_state(selected);view=AquariumView(lambda:state,ESPECIES)
        for detail in (1,2):
            cold=[]
            for i in range(30):
                aquarium_species_image.cache_clear()
                t=time.perf_counter_ns();view.render_image(i*.2,detail)
                cold.append((time.perf_counter_ns()-t)/1e6)
            for i in range(120):view.render_image(i*.066,detail)
            samples=[]
            for i in range(1200):
                t=time.perf_counter_ns();view.render_image(i*.066,detail)
                samples.append((time.perf_counter_ns()-t)/1e6)
            s=sorted(samples)
            timing[name+'_'+str(detail)+'x']=dict(n=len(s),median_ms=statistics.median(s),
                p95_ms=s[math.ceil(.95*len(s))-1],p99_ms=s[math.ceil(.99*len(s))-1],
                max_ms=max(s),mean_ms=statistics.mean(s),timer_interval_ms=view.timer.interval())
            timing[name+'_'+str(detail)+'x']['cold']=dict(n=len(cold),median_ms=statistics.median(cold),
                p95_ms=sorted(cold)[math.ceil(.95*len(cold))-1],max_ms=max(cold))
        view.close()
    report=dict(python=platform.python_version(),pyside=pyside_version,platform=platform.system(),
        source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip() if (root/'.git').exists() else 'archive',
        animated=improved,method='30 cache-cleared renders, 120 warmups + 1200 warm renders, per scene/detail, serial, no sleeps. Microbenchmark only.',
        timings=timing,save_created=(out/'synthetic-never-written.json').exists())
    (out/'performance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not args.benchmark_only:
        # Master sequences distinguish deformation from movement across the tank.
        showcase=['lambari','tilapia_do_nilo','carpa_comum','traira','cavalinho_do_mar_pigmeu','peixe_lua']
        strip=QImage(1192,830,QImage.Format_ARGB32_Premultiplied);strip.fill(QColor('#182c39'))
        p=QPainter(strip);p.setFont(QFont('Segoe UI',12,QFont.Bold));p.setPen(QColor('#e1ead8'))
        p.drawText(20,28,'Cauda e nadadeiras | oito quadros reais | ampliação 2x')
        for row,id_ in enumerate(showcase):
            y=52+row*128;p.setFont(QFont('Segoe UI',10,QFont.Bold));p.setPen(QColor('#e1ead8'))
            p.drawText(20,y,ESPECIES[id_]['nome'])
            for frame in range(8):
                p.fillRect(20+frame*145,y+8,140,105,QColor('#234854'))
                p.drawImage(QRectF(20+frame*145,y+8,140,93),aquarium_species_image(id_,2,frame))
                p.setFont(QFont('Segoe UI',7));p.setPen(QColor('#c4d5cb'));p.drawText(24+frame*145,y+109,str(frame))
        p.end();strip.save(str(out/'quadros.png'))
        for name,selected in [('piloto',scenes['pilot']),('formas',scenes['special'])]:
            state=synthetic_state(selected);view=AquariumView(lambda:state,ESPECIES)
            frames=[]
            for i in range(48):frames.append(pil(view.render_image(i*.08,2)).convert('RGB'))
            frames[0].save(out/('aquario-'+name+'.gif'),save_all=True,append_images=frames[1:],duration=80,loop=0)
            for phase in (0.,.4,1.2):view.render_image(phase,2).save(str(out/(name+'-'+str(phase)+'.png')))
            view.close()
        frames=[]
        for frame in range(8):
            img=QImage(1000,330,QImage.Format_ARGB32_Premultiplied);img.fill(QColor('#234854'));p=QPainter(img)
            for n,id_ in enumerate(('lambari','cavalinho_do_mar_pigmeu','peixe_lua')):
                p.drawImage(QRectF(16+n*330,25,300,200),aquarium_species_image(id_,2,frame))
                p.setFont(QFont('Segoe UI',12));p.setPen(QColor('#e1ead8'));p.drawText(20+n*330,265,ESPECIES[id_]['nome'])
            p.setFont(QFont('Segoe UI',10));p.drawText(20,307,'Ampliação para revisão do movimento | quadro '+str(frame))
            p.end();frames.append(pil(img).convert('RGB'))
        frames[0].save(out/'movimento-ampliado.gif',save_all=True,append_images=frames[1:],duration=200,loop=0)
        class Host(QWidget):
            def __init__(self):super().__init__();self.estado=synthetic_state()
            def _commit(self,_):raise RuntimeError('Visual capture forbids persistence.')
        host=Host();dialog=MuseuDialog(host);dialog.setAttribute(Qt.WA_DontShowOnScreen,True);dialog.show();app.processEvents()
        for width,height in ((640,700),(320,568)):
            dialog.resize(width,height);app.processEvents();dialog.aquario.timer.stop();dialog.aquario.phase=.4;app.processEvents()
            if (dialog.width(),dialog.height())!=(width,height):raise AssertionError('Viewport could not be set.')
            assert dialog.grab().save(str(out/('museu-'+str(width)+'.png')))
        dialog.close();host.close()
        files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in [root/'pesca_museu_ui.py',root/'pesca_museu_visual.py',root/'assets/aquario_especies.json',root/'assets/aquario_movimento.json']}
        manifest=dict(code_sha=report['source_commit'],files=files,
            outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()},
            scope='Synthetic in-memory visual verification; no game simulation or persistence.')
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'tests':checks.get('tests'),'benchmarks':timing,'save_created':report['save_created']},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
