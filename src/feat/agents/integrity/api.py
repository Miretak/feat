import operator

from feat.agents.integrity import integrity_agent
from feat.common import defer
from feat.database import conflicts
from feat.gateway.application import featmodels
from feat.gateway import models
from feat.models import model, value, call, getter, response, action, effect

from feat.models.interface import IModel, InvalidParameters, ActionCategories


@featmodels.register_model
@featmodels.register_adapter(integrity_agent.IntegrityAgent, IModel)
class IntegrityAgent(models.Agent):
    model.identity('feat.integrity_agent')

    model.child('replications', model='feat.integrity_agent.replications',
                label="Replications")


@featmodels.register_model
class Replications(model.Collection):
    model.identity('feat.integrity_agent.replications')
    model.child_names(call.model_call('get_names'))
    model.child_view(getter.model_get('get_status'))
    model.child_model('feat.integrity_agent.replications.NAME')
    model.child_meta('json', 'render-inline')

    def init(self):
        state = self.source._get_state()
        self.connection = state.replicator
        self.config = state.db_config
        d = conflicts.get_replication_status(self.connection,
                                             self.config.name)
        d.addCallback(defer.inject_param, 2, setattr, self, 'statuses')
        return d

    def get_names(self):
        return self.statuses.keys()

    def get_status(self, name):
        rows = self.statuses.get(name)
        if not rows:
            return
        rows.sort(key=operator.itemgetter(0), reverse=True)
        return rows[0]

    model.create('post',
                 call.model_perform('create_replication'),
                 response.created('Replication set up'),
                 params=[action.Param('target', value.String())])

    def create_replication(self, target):
        if target in self.statuses:
            status = sorted(self.statuses[target],
                            key=operator.itemgetter(0), reverse=True)[0]
            seq, continuous, status, r_id = status
            if continuous:
                msg = 'Continuous replication to this target already exists'
                raise InvalidParameters(params=dict(target=msg))
        doc = {'source': unicode(self.config.name), 'target': target,
               'continuous': True, 'filter': u'featjs/replication'}
        return self.connection.save_document(doc)


@featmodels.register_model
class Replication(model.Model):
    model.identity('feat.integrity_agent.replications.NAME')
    model.attribute('last_seq', value.Integer(),
                    getter=getter.model_attr('seq'))
    model.attribute('continuous', value.Integer(),
                    getter=getter.model_attr('continuous'))
    model.attribute('status', value.String(),
                    getter=getter.model_attr('status'))
    model.attribute('id', value.String(),
                    getter=getter.model_attr('id'))

    def init(self):
        self.seq, self.continuous, self.status, self.id = self.view

    model.action('pause',
                 action.MetaAction.new('perform_pause',
                                       ActionCategories.command,
                                       effects=[effect.context_value('key'),
                                                call.model_perform('pause'),
                                                response.done('done')],
                                       result_info=value.Response()))

    def pause(self, value):
        if not self.continuous:
            return
        state = self.source._get_state()
        connection = state.replicator

        d = connection.query_view(conflicts.Replications,
                                  key=('target', value),
                                  include_docs=True)

        def delete_continuous(replications):
            d = defer.succeed(None)
            for replication in replications:
                if replication.get('continuous'):
                    d.addCallback(defer.drop_param,
                                  connection.delete_document,
                                  replication)
            return d

        d.addCallback(defer.keep_param, delete_continuous)

        def create_1_repl(replications):
            if not replications:
                return
            r = replications[0]
            doc = {'source': r['source'], 'target': r['target'],
                   'filter': r['filter']}
            return connection.save_document(doc)

        d.addCallback(create_1_repl)
        return d
