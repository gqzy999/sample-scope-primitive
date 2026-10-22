"""Behavioral tests using a minimal GenVM boundary stub; not network consensus tests."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

class Map(dict):
    @classmethod
    def __class_getitem__(cls, key): return cls
class Return:
    def __init__(self, data): self.calldata=data

def identity(fn): return fn
source='Research use allowed. No grinding. No transfer. Return residue.'
answer={g:{'status':'ALLOW','quote':'Research use allowed.'} for g in ('purpose','destructive','transfer','return')}
def prompt(_, **kwargs):
    import json
    return json.dumps(answer)
def consensus(leader, validator):
    result=leader()
    if not validator(Return(result)): raise ValueError('Consensus disagreement')
    return result
message=types.SimpleNamespace(sender_address='curator')
gl=types.SimpleNamespace(Contract=object,public=types.SimpleNamespace(write=identity,view=identity),message=message,
    nondet=types.SimpleNamespace(web=types.SimpleNamespace(render=lambda *a,**k:source),exec_prompt=prompt),
    vm=types.SimpleNamespace(UserError=ValueError,Return=Return,run_nondet_unsafe=consensus))
sys.modules['genlayer']=types.SimpleNamespace(gl=gl,TreeMap=Map,Address=str)
spec=importlib.util.spec_from_file_location('scope',Path(__file__).parents[1]/'contracts/sample_scope.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        message.sender_address='curator';self.c=m.SampleScope();self.c.records=Map()
        self.register()
    def register(self,key='a',url='https://publications.iodp.org/scientific_prospectus/353/353sp_10.htm'):
        self.c.register(key,'core 1',url,'Non-destructive scan, no transfer, return residue')
    def state(self):return self.c._load('a')['state']
    def test_model_json_wrapper(self):
        import json
        self.assertEqual(m.parse_model_response("```json\n" + json.dumps(answer) + "\n```"), answer)
        self.assertEqual(m.parse_model_response(answer), answer)
        with self.assertRaises(ValueError):m.parse_model_response("Here is the answer: {}")
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):self.register()
    def test_url_allowlist(self):
        for u in ['http://publications.iodp.org/a','https://publications.iodp.org.evil/a','https://127.0.0.1/a']:
            with self.subTest(url=u),self.assertRaises(ValueError):self.register('other',u)
    def test_unknown_record(self):
        with self.assertRaises(ValueError):self.c.assess('absent')
    def test_requester_only(self):
        message.sender_address='other'
        with self.assertRaises(ValueError):self.c.assess('a')
    def test_authorization_before_assessment(self):
        with self.assertRaises(ValueError):self.c.decide('a',True,'ok')
    def test_full_lifecycle(self):
        self.c.assess('a');self.assertEqual(self.state(),'WITHIN_SCOPE')
        self.c.decide('a',True,'Allocation approval reference 1');self.assertEqual(self.state(),'AUTHORIZED')
        self.c.close('a','Residue received, report archived');self.assertEqual(self.state(),'CLOSED')
        with self.assertRaises(ValueError):self.c.close('a','again')
    def test_curator_only(self):
        self.c.assess('a');message.sender_address='other'
        with self.assertRaises(ValueError):self.c.decide('a',True,'ok')
    def test_repeat_assessment(self):
        self.c.assess('a')
        with self.assertRaises(ValueError):self.c.assess('a')
    def test_decline_terminal(self):
        self.c.assess('a');self.c.decide('a',False,'No allocation');self.assertEqual(self.state(),'DECLINED')
        with self.assertRaises(ValueError):self.c.close('a','return')
    def test_close_requires_authorized(self):
        with self.assertRaises(ValueError):self.c.close('a','done')
    def test_note_required(self):
        self.c.assess('a')
        with self.assertRaises(ValueError):self.c.decide('a',True,' ')
    def test_bounds(self):
        with self.assertRaises(ValueError):self.c.register('b','core','https://publications.iodp.org/a','x'*4001)
    def test_status_truth_table(self):
        import itertools
        for states in itertools.product(('ALLOW','DENY','REVIEW'),repeat=4):
            data={g:{'status':s} for g,s in zip(m.GATES,states)}
            want='BLOCKED' if 'DENY' in states else 'CURATOR_REVIEW' if 'REVIEW' in states else 'WITHIN_SCOPE'
            self.assertEqual(m.outcome(data),want)
    def test_fabricated_quote_rejected(self):
        import copy
        bad=copy.deepcopy(answer);bad['purpose']['quote']='Made up'
        with self.assertRaises(ValueError):m.validate_result(bad,source)
    def test_missing_gate(self):
        with self.assertRaises(ValueError):m.validate_result({},source)
    def test_silence_review(self):
        data={g:{'status':'REVIEW','quote':''} for g in m.GATES}
        self.assertEqual(m.outcome(m.validate_result(data,source)),'CURATOR_REVIEW')
    def test_validator_rejects_forged_quote(self):
        import copy
        original=gl.vm.run_nondet_unsafe
        def attack(leader,validator):
            data=copy.deepcopy(leader());data['gates']['purpose']['quote']='forged permission'
            self.assertFalse(validator(Return(data)))
            raise ValueError('Rejected')
        gl.vm.run_nondet_unsafe=attack
        try:
            with self.assertRaises(ValueError):self.c.assess('a')
            self.assertEqual(self.state(),'REGISTERED')
        finally:gl.vm.run_nondet_unsafe=original
    def test_blocked_cannot_authorize(self):
        r=self.c._load('a');r['state']='BLOCKED';self.c._save('a',r)
        with self.assertRaises(ValueError):self.c.decide('a',True,'override')

if __name__=='__main__':unittest.main()
