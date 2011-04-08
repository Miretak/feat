# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
from twisted.trial.unittest import SkipTest, FailTest
from twisted.internet import defer

from feat.test import common
from feat.common import delay as delay_module
from feat.simulation import driver
from feat.agencies import replay


attr = common.attr
time = common.time
delay = common.delay
delay_errback = common.delay_errback
delay_callback = common.delay_callback
break_chain = common.break_chain
break_callback_chain = common.break_callback_chain
break_errback_chain = common.break_errback_chain


class IntegrationTest(common.TestCase):
    pass


def jid2str(jid):
    if isinstance(jid, basestring):
        return str(jid)
    return "-".join([str(i) for i in jid])


def format_journal(journal, prefix=""):

    def format_call(funid, args, kwargs):
        params = []
        if args:
            params += [repr(a) for a in args]
        if kwargs:
            params += ["%r=%r" % i for i in kwargs.items()]
        return [funid, "(", ", ".join(params), ")"]

    parts = []
    for _, jid, funid, fid, fdepth, args, kwargs, se, result in journal:
        parts += [prefix, jid2str(jid), ": \n"]
        parts += [prefix, " "*4]
        parts += format_call(funid, args, kwargs)
        parts += [":\n"]
        parts += [prefix, " "*8, "FIBER ", str(fid),
                  " DEPTH ", str(fdepth), "\n"]
        if se:
            parts += [prefix, " "*8, "SIDE EFFECTS:\n"]
            for se_funid, se_args, se_kwargs, se_effects, se_result in se:
                parts += [prefix, " "*12]
                parts += format_call(se_funid, se_args, se_kwargs)
                parts += [":\n"]
                if se_effects:
                    parts += [prefix, " "*16, "EFFECTS:\n"]
                    for eid, args, kwargs in se_effects:
                        parts += [prefix, " "*20]
                        parts += format_call(eid, args, kwargs) + ["\n"]
                parts += [prefix, " "*16, "RETURN: ", repr(se_result), "\n"]
        parts += [prefix, " "*8, "RETURN: ", repr(result), "\n\n"]
    return "".join(parts)


class SimulationTest(common.TestCase):

    configurable_attributes = ['skip_replayability']
    skip_replayability = False

    def setUp(self):
        delay_module.time_scale = 1
        self.driver = driver.Driver()
        return self.prolog()

    def process(self, script):
        d = self.cb_after(None, self.driver._parser, 'on_finish')
        self.driver.process(script)
        return d

    def get_local(self, *names):
        results = map(lambda name: self.driver._parser.get_local(name), names)
        if len(results) == 1:
            return results[0]
        else:
            return tuple(results)

    def set_local(self, name, value):
        self.driver._parser.set_local(value, name)

    def get_agent_journal(self, agent):
        for agency in self.driver._agencies:
            for medium in agency._agents:
                if agent.journal_id == medium.get_agent().journal_id:
                    aid = agent.get_descriptor().doc_id
                    return [entry for entry in agency._journal_entries
                            if entry and entry[0] == aid]
        return []

    def format_agent_journal(self, agent, prefix=""):
        return format_journal(self.get_agent_journal(agent), prefix)

    @defer.inlineCallbacks
    def tearDown(self):
        for x in self.driver.iter_agents():
            yield x.wait_for_listeners_finish()
        yield common.TestCase.tearDown(self)
        if not self.skip_replayability:
            self.log("Test finished, now validating replayability.")
            for agency in self.driver._agencies:
                self._validate_replay_on_agency(agency)
        else:
            print "\n\033[91mFIXME: \033[0mReplayability test skipped: %s\n" %\
                  self.skip_replayability

    def _validate_replay_on_agency(self, agency):
        for agent in agency._agents:
            self._validate_replay_on_agent(agency, agent)

    def _validate_replay_on_agent(self, agency, agent):
        aid = agent.get_descriptor().doc_id
        self.log("Validating replay of %r with id: %s",
                 agent.agent.__class__.__name__, aid)

        entries = [entry for entry in agency._journal_entries\
                   if entry and entry[0] == aid]
        self.log("Found %d entries of this agent.", len(entries))

        r = replay.Replay(iter(entries), aid)
        for entry in r:
            entry.apply()

        agent_snapshot, listeners = agent.snapshot_agent()
        self.log("Replay complete. Comparing state of the agent and his "
                 "%d listeners.", len(listeners))
        self.assertEqual(agent_snapshot._get_state(), r.agent._get_state())

        listeners_from_replay = [obj for obj in r.registry.values()
                                 if obj.type_name.endswith('-medium')]

        self.assertEqual(len(listeners_from_replay), len(listeners))
        for from_snapshot, from_replay in zip(listeners,
                                              listeners_from_replay):
            self.assertEqual(from_snapshot._get_state(),
                             from_replay._get_state())

    @defer.inlineCallbacks
    def wait_for(self, check, timeout, freq=0.5):
        assert callable(check)
        waiting = 0

        while True:
            if check():
                break
            self.info('Check %r still negative, sleping %r seconds.',
                      check.__name__, freq)
            waiting += freq
            if waiting > timeout:
                raise FailTest('Timeout error waiting for check %r.',
                               check.__name__)
            yield common.delay(None, freq)

    def count_agents(self):
        return len([x for x in self.driver.iter_agents()])
