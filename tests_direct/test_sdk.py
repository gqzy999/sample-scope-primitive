"""Official GenLayer direct runner with real SDK/storage, mocked web and model I/O."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from gltest.direct import VMContext, deploy_contract, create_address

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'fixtures/scope_cases.json').read_text())['cases']
GATES=('purpose','destructive','transfer','return')
URL='https://publications.iodp.org/scientific_prospectus/353/353sp_10.htm'

@pytest.fixture
def env():
    vm=VMContext();vm.sender=create_address('curator')
    with vm.activate():
        c=deploy_contract(ROOT/'contracts/sample_scope.py',vm,sdk_version='v0.3.0-rc7')
        yield vm,c

def setup(vm,c,case):
    data={g:{'status':s,'quote':q} for g,s,q in zip(GATES,case['statuses'],case['quotes'])}
    vm.mock_web(r'https://publications\.iodp\.org/.*',{'method':'GET','status':200,'body':case['policy']})
    vm.mock_llm('Evaluate a geological sample',json.dumps(data))
    c.register('core-1','Synthetic core reference',URL,case['plan'])
    return data

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['name'])
def test_policy_cases_and_independent_validator(env,case):
    vm,c=env;setup(vm,c,case);c.assess('core-1')
    record=json.loads(c.get_request('core-1'))
    assert record['state']==case['outcome']
    assert record['policy_hash']==hashlib.sha256(case['policy'].encode()).hexdigest()
    assert vm.run_validator() is True

def test_complete_history_preserves_authorization_and_return(env):
    vm,c=env;setup(vm,c,CASES[0]);c.assess('core-1')
    c.decide('core-1',True,'Allocation reference 42')
    c.close('core-1','Residue returned; report reference 56')
    r=json.loads(c.get_request('core-1'))
    assert [x['state'] for x in r['history']]==['REGISTERED','WITHIN_SCOPE','AUTHORIZED','CLOSED']
    assert r['history'][2]['note']=='Allocation reference 42'
    assert r['history'][3]['note']=='Residue returned; report reference 56'

def test_real_sdk_sender_authorization(env):
    vm,c=env;setup(vm,c,CASES[0])
    with vm.prank(create_address('other')):
        with vm.expect_revert('Only requester'):c.assess('core-1')
    c.assess('core-1')
    with vm.prank(create_address('other')):
        with vm.expect_revert('Curator only'):c.decide('core-1',True,'unauthorized')
    assert json.loads(c.get_request('core-1'))['state']=='WITHIN_SCOPE'

def test_validator_rejects_changed_gate(env):
    vm,c=env;data=setup(vm,c,CASES[0]);c.assess('core-1')
    forged={'gates':copy.deepcopy(data),'policy_hash':hashlib.sha256(CASES[0]['policy'].encode()).hexdigest()}
    forged['gates']['purpose']['status']='DENY'
    assert vm.run_validator(leader_result=forged) is False

def test_validator_rejects_fabricated_quote_and_missing_hash(env):
    vm,c=env;data=setup(vm,c,CASES[0]);c.assess('core-1')
    forged={'gates':copy.deepcopy(data),'policy_hash':hashlib.sha256(CASES[0]['policy'].encode()).hexdigest()}
    forged['gates']['purpose']['quote']='Unrestricted destructive transfer permitted.'
    assert vm.run_validator(leader_result=forged) is False
    assert vm.run_validator(leader_result={'gates':data}) is False

def test_validator_rejects_different_source_snapshot(env):
    vm,c=env;data=setup(vm,c,CASES[0]);c.assess('core-1')
    forged={'gates':data,'policy_hash':'0'*64}
    assert vm.run_validator(leader_result=forged) is False

def test_bad_model_json_does_not_advance_request(env):
    vm,c=env;c.register('core-1','core',URL,'Non-destructive scan')
    vm.mock_web('.*',{'method':'GET','status':200,'body':'Permission not specified.'})
    vm.mock_llm('.*','not valid JSON')
    with vm.expect_revert():c.assess('core-1')
    assert json.loads(c.get_request('core-1'))['state']=='REGISTERED'
