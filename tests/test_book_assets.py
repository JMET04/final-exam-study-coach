"""Behavior checks for real portable assets and malformed contributed archives."""
from pathlib import Path
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('book_asset',ROOT/'optional/book-spirit/scripts/book_asset.py')
asset=importlib.util.module_from_spec(spec);spec.loader.exec_module(asset)
LIB=Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else ROOT/'optional/book-library'

class Assets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.book=Path(cls.tmp.name)/'concrete'
        cls.archive=LIB/'books/book_7d6d67c24e8a4a47/book.zip'
        asset.extract(cls.archive,cls.book)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def test_catalog_and_independent_coverage(self):
        result=asset.validate_catalog(LIB)
        self.assertGreaterEqual(result['books_validated'],2)
        c=asset.manifest(self.book)['coverage']
        self.assertFalse(c['whole_book_expert_complete']);self.assertFalse(c['whole_book_animation_complete'])
        self.assertGreater(c['fresh_topics'],0)
    def test_topic_routing_and_conditions(self):
        matches=asset.topics(self.book,'中性轴',5)['topics']
        self.assertTrue(any(t['topic_key']=='neutral-axis' for t in matches))
        t=asset.topic(self.book,'neutral-axis',[],50000)['topic']['body']
        self.assertTrue(t['facets']);self.assertTrue(t.get('always_facets'))
    def test_single_segment_context_without_api(self):
        c=asset.context(self.book,'neutral-axis-identities','equivalent-depth',0.5,'x为什么和xc不同')
        self.assertEqual(c['segment_id'],'equivalent-depth')
        self.assertIn('0.8',c['narration']);self.assertIn('xc',c['symbols'])
        self.assertNotIn('segments',c);self.assertNotIn('api_key',c)
        for frame in c['keyframes']: self.assertTrue((self.book/frame['path']).is_file())
    def test_missing_point_and_invalid_progress(self):
        with self.assertRaises(ValueError): asset.context(self.book,'not-built','main',0,'why')
        with self.assertRaises(ValueError): asset.context(self.book,'neutral-axis-identities','actual-neutral',float('nan'),'why')
    def test_existing_destination_is_not_overwritten(self):
        with self.assertRaises(ValueError): asset.extract(self.archive,self.book)
    def rewritten(self,mutate):
        with zipfile.ZipFile(self.archive) as z: data={n:z.read(n) for n in z.namelist()}
        mutate(data);p=Path(self.tmp.name)/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:
            for n,b in data.items(): z.writestr(n,b)
        return p
    def test_tamper_detected(self):
        p=self.rewritten(lambda d:d.__setitem__('knowledge/topics.jsonl',b'{}\n'))
        with self.assertRaises(ValueError): asset.verify(p)
    def test_path_traversal_and_source_pdf_rejected(self):
        for name in ['../escape.json','C:/private.json','source.pdf']:
            p=self.rewritten(lambda d:d.__setitem__(name,b'{}'))
            with self.assertRaises(ValueError): asset.verify(p)
    def test_false_completion_rejected(self):
        def change(d):
            m=json.loads(d['manifest.json']);m['coverage']['whole_book_expert_complete']=True;d['manifest.json']=json.dumps(m).encode()
        p=self.rewritten(change)
        with self.assertRaises(ValueError): asset.verify(p)
    def test_missing_keyframe_rejected_even_with_matching_file_manifest(self):
        def change(d):
            name=next(n for n in d if n.endswith('.svg'))
            del d[name]
            m=json.loads(d['manifest.json']);del m['files'][name]
            d['manifest.json']=json.dumps(m).encode()
        with self.assertRaisesRegex(ValueError,'keyframe'): asset.verify(self.rewritten(change))
    def test_facet_selection_keeps_required_facets(self):
        whole=asset.topic(self.book,'neutral-axis',[],50000)['topic']['body']
        first=whole['facets'][0]['id']
        selected=asset.topic(self.book,'neutral-axis',[first],50000)['topic']['body']
        self.assertTrue(set(whole['always_facets'])<={f['id'] for f in selected['facets']})
    def test_skill_only_install_includes_the_same_tool(self):
        canonical=ROOT/'optional/book-spirit/scripts/book_asset.py'
        installed=ROOT/'optional/book-spirit/skills/book-spirit/scripts/book_asset.py'
        self.assertEqual(canonical.read_bytes(),installed.read_bytes())
    def test_context_budget_does_not_truncate_conditions(self):
        with self.assertRaises(ValueError): asset.topic(self.book,'neutral-axis',[],10)

if __name__=='__main__': unittest.main()
