import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'content/state.json';state=json.loads(p.read_text());articles=json.loads((root/'content/articles.json').read_text());queue=[a for a in articles if not a['published']];i=state['released_count']
if i<len(queue):
 state['released_count']=i+1;p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');print('released:',queue[i]['title'])
else:print('queue empty; no changes')
