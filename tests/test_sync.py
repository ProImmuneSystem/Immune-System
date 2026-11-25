import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('sync_wp',Path(__file__).resolve().parents[1]/'scripts/sync_wp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SyncTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.oldroot,self.oldstate=m.ROOT,m.STATE;m.ROOT=self.root;m.STATE=self.root/'_data/sync_state.json';(self.root/'_posts').mkdir()
  self.snapshot=json.loads((Path(__file__).resolve().parents[2]/'wp-snapshot.json').read_text()) if (Path(__file__).resolve().parents[2]/'wp-snapshot.json').exists() else None
  self.posts=[{'ID':3,'title':'테스트 &amp; 글','slug':'test','date':'2026-11-25T10:00:00+09:00','modified':'2026-11-25T10:00:00+09:00','URL':'https://proimmunesystem.wordpress.com/2026/11/25/test/','content':'<p>본문</p><img src="https://proimmunesystem.wordpress.com/wp-content/uploads/test.jpg?w=30" srcset="a 1w, b 2w"><a href="https://proimmunesystem.wordpress.com/a/">링크</a>','excerpt':'<p>요약</p>','categories':{'면역세포':{'slug':'immune-cells'}},'tags':{},'featured_image':''}]
 def tearDown(self):m.ROOT=self.oldroot;m.STATE=self.oldstate;self.temp.cleanup()
 def test_idempotence_and_preserve_unknown(self):
  (self.root/'_posts'/'manual.html').write_text('manual')
  m.sync(self.posts,True);before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()};m.sync(self.posts,True);self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
  self.assertIn('manual', (self.root/'_posts'/'manual.html').read_text())
  text=(self.root/'_posts'/'2026-11-25-test.html').read_text();self.assertIn('https://proimmunesystem.wordpress.com/wp-content/uploads/test.jpg',text);self.assertNotIn('srcset=',text);self.assertIn('{{ site.baseurl }}{% raw %}/a/',text)
 def test_delete_only_mirrored_and_empty_fails_closed(self):
  m.sync(self.posts,True)
  with self.assertRaises(ValueError):m.sync([],True)
  self.assertTrue((self.root/'_posts'/'2026-11-25-test.html').exists())
  second=dict(self.posts[0],ID=4,slug='next',URL='https://proimmunesystem.wordpress.com/2026/11/25/next/')
  m.sync([second],True);self.assertFalse((self.root/'_posts'/'2026-11-25-test.html').exists())
 def test_bad_pagination_never_returns_posts(self):
  with patch.object(m,'fetch',return_value=b'{"found":2,"posts":[]}'):
   with self.assertRaises(ValueError):m.get_posts()
if __name__=='__main__':unittest.main()
