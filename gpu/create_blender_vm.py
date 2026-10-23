"""Create one isolated H100 worker; never blindly repeat a lost creation request."""
import datetime
import json
from pathlib import Path
import subprocess
import ipaddress
import sys
from hyperstack import api

assert len(sys.argv) in (2, 3), 'Pass your public IPv4 and an optional unique run name'
run_name = sys.argv[2] if len(sys.argv) == 3 else 'visual-v1'
assert 1 <= len(run_name) <= 40 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in run_name)
run = Path(__file__).resolve().parent / 'runs' / run_name
run.mkdir(parents=True, exist_ok=True)
name = 'umrah-' + run_name + '-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
ssh_source = str(ipaddress.IPv4Address(sys.argv[1])) + '/32'
rates = [float(p['value']) for p in api('GET', '/pricebook')
         if p.get('name') == 'H100-80G-PCIe-spot' and not p.get('start_time') and not p.get('end_time')]
assert len(rates) == 1 and 0 < rates[0] <= 2.0, 'Refresh pricing: current H100 spot GPU rate exceeds this batch\'s $2/hour ceiling or is ambiguous'
existing = api('GET', '/core/virtual-machines?page=1&pageSize=100')['instances']
assert not any(vm['name'] == name for vm in existing), 'Worker already exists: inspect it instead of creating another'
assert not (run / 'instance.json').exists(), 'Prior run exists: inspect it before starting another'
keys = api('GET', '/core/keypairs')['keypairs']
key = next(k for k in keys if k['name'] == 'hyperstack')
public = subprocess.check_output(['ssh-keygen', '-y', '-f', str(Path.home() / '.ssh/hyperstack')], text=True)
assert public.split()[:2] == key['public_key'].split()[:2], 'SSH key mismatch'
boot = '''#!/bin/bash
set -eu
ssh-keygen -A
echo "UMRAH_HOST_KEY:$(cat /etc/ssh/ssh_host_ed25519_key.pub)" > /dev/console
# Finite worker lifetime even if the local process disconnects. Host-side deletion
# still follows successful retrieval; shutdown alone does not remove billed disk.
shutdown -h +180
apt-get update -qq
apt-get install -y -qq python3-venv libgl1 libxi6 libxrender1 libxfixes3 libxkbcommon0 libsm6
mkdir -p /opt/umrah
python3 -m venv /opt/umrah/venv
/opt/umrah/venv/bin/pip install --disable-pip-version-check uv==0.9.7
/opt/umrah/venv/bin/uv venv --python 3.11 --managed-python /opt/umrah/render-env
/opt/umrah/venv/bin/uv pip install --python /opt/umrah/render-env/bin/python bpy==5.0.1 Pillow==11.3.0 numpy==1.26.4
nvidia-smi > /opt/umrah/gpu.txt
touch /opt/umrah/ready
'''
request = {'name': name, 'environment_name': 'default-CANADA-1',
           'flavor_name': 'n3-H100x1-bigroot-spot',
           'image_name': 'Ubuntu Server 24.04 LTS R570 CUDA 12.8 with Docker',
           'key_name': 'hyperstack', 'count': 1, 'assign_floating_ip': True,
           'user_data': boot, 'security_rules': [
               {'direction': 'ingress', 'ethertype': 'IPv4', 'protocol': 'tcp',
                'port_range_min': 22, 'port_range_max': 22, 'remote_ip_prefix': ssh_source}]}
(run / 'request.json').write_text(json.dumps(request, indent=2))
# A timestamp and unique name are persisted BEFORE billing can start.
(run / 'creation-intent.json').write_text(json.dumps({'name': name, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}))
result = api('POST', '/core/virtual-machines', request)
(run / 'creation-result.json').write_text(json.dumps(result, indent=2))
rows = result.get('instances', result.get('results', []))
assert len(rows) == 1 and rows[0]['name'] == name, 'Ambiguous result: inspect inventory; do not retry'
vm = rows[0]
(run / 'instance.json').write_text(json.dumps({'id': vm['id'], 'name': name, 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'gpuHourlyUsd': rates[0]}, indent=2))
print(json.dumps({'id': vm['id'], 'name': name, 'status': vm['status']}))
