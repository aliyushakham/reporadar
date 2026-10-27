"""Check portable n8n export structure, not an n8n execution test."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
workflow = json.loads((root/'workflows/reporadar-index.json').read_text())
names = {node['name'] for node in workflow['nodes']}
assert len(names) == len(workflow['nodes'])
assert not workflow['active']
assert workflow['id'] == 'RepoRadarIndex'
import uuid
uuid.UUID(workflow['versionId'])
for source, outputs in workflow['connections'].items():
    assert source in names
    for branch in outputs['main']:
        for edge in branch:
            assert edge['node'] in names
scan = next(n for n in workflow['nodes'] if n['id']=='scan')
assert scan['parameters']['method']=='POST'
assert scan['parameters']['jsonBody']=='{}'
assert scan['onError']=='continueErrorOutput'
assert len(workflow['connections'][scan['name']]['main']) == 2
print('Workflow structure validated; execution requires a running n8n instance.')
