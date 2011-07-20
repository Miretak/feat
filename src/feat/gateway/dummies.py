import os

from feat.agents.base import agent, descriptor, partners
from feat.agents.common import monitor


class StandalonePartners(agent.Partners):

    default_role = u'standalone'


class DummyStandalone(agent.BaseAgent):

    partners_class = StandalonePartners

    standalone = True

    @staticmethod
    def get_cmd_line():
        src_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..'))
        command = os.path.join(src_path, 'feat', 'bin', 'standalone.py')
        logfile = os.path.join(src_path, 'standalone.log')
        args = ['-i', 'feat.test.test_agencies_net_agency',
                '-l', logfile]
        env = dict(PYTHONPATH=src_path, FEAT_DEBUG='5')
        return command, args, env

    def startup(self):
        self.startup_monitoring()


class DummyAgent(agent.BaseAgent):

    def startup(self):
        self.startup_monitoring()


@descriptor.register('dummy_buryme_standalone')
class DummyBuryMeStandaloneDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_buryme_standalone')
class DummyBuryMeStandalone(DummyStandalone):
    restart_strategy = monitor.RestartStrategy.buryme


@descriptor.register('dummy_local_standalone')
class DummyLocalStandaloneDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_local_standalone')
class DummyLocalStandalone(DummyStandalone):
    restart_strategy = monitor.RestartStrategy.local


@descriptor.register('dummy_wherever_standalone')
class DummyWhereverStandaloneDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_wherever_standalone')
class DummyWhereverStandalone(DummyStandalone):
    restart_strategy = monitor.RestartStrategy.wherever


@descriptor.register('dummy_buryme_agent')
class DummyBuryMeAgentDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_buryme_agent')
class DummyBuryMeAgent(DummyAgent):
    restart_strategy = monitor.RestartStrategy.buryme


@descriptor.register('dummy_local_agent')
class DummyLocalAgentDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_local_agent')
class DummyLocalAgent(DummyAgent):
    restart_strategy = monitor.RestartStrategy.local


@descriptor.register('dummy_wherever_agent')
class DummyWhereverAgentDescriptor(descriptor.Descriptor):
    pass


@agent.register('dummy_wherever_agent')
class DummyWhereverAgent(DummyAgent):
    restart_strategy = monitor.RestartStrategy.wherever
