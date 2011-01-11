from zope.interface import Interface, Attribute

__all__ = ["IAgentFactory", "IAgencyAgent", "IAgencyAgent"]


class IAgentFactory(Interface):
    '''Create an agent implementing L{IAgent}. Used by the agency when
    starting an agent.'''

    def __call__(medium, *args, **kwargs):
        pass


class IAgencyAgent(Interface):
    '''Agency part of an agent. Used as a medium by the agent
    L{IAgent} implementation.'''

    agent = Attribute("L{IAgent}")
    agency = Attribute("L{IAgency}")

    def get_descriptor():
        '''
        Return the copy of the descriptor.
        '''

    def update_descriptor(desc):
        '''
        Save the descriptor into the database. This method should be used
        instead of save_document, because agency side of implementation needs
        to keep track of the changes.

        @param desc: Descriptor to save.
        @type desc: feat.agents.base.descriptor.Descriptor
        @returns: Deferred
        '''

    def register_interest(factory):
        '''Registers an interest in a contract or a request.'''

    def revoke_interest(factory):
        '''Revokes any interest in a contract or a request.'''

    def initiate_protocol(factory, recipients, *args, **kwargs):
        '''
        Initiates a contract or a request.

        @type recipients: L{IRecipients}
        @rtype: L{IInitiator}
        @returns: Instance of protocols initiator
        '''

    def retrying_protocol(self, factory, recipients, max_retries,
                         initial_delay, max_delay, *args, **kwargs):
        '''
        Initiates the protocol which will get restart if it fails.
        The restart will be delayed with exponential growth.

        Extra params comparing to L{IAgencyAgent.initiate_protocol}:

        @param max_retries: After how many retries to give up. Def. None: never
        @param initial_delay: Delay before the first retry.
        @param max_delay: Miximum delay to wait (above it it will not grow).
        @returns: L{RetryingProtocol}
        '''

    def get_time():
        '''
        Use this to get current time. Should fetch the time from NTP server

        @returns: Number of seconds since epoch
        '''

    def send_msg(recipient, message):
        '''
        Sends message to the recipients.

        @param recipient: Message destination
        @type recipient: L{IRecipient}
        @return: Message that was sent
        '''

    def save_document(document):
        '''
        Save the document into the database. Document might have been loaded
        from the database before, or has just been constructed.

        If the doc_id
        property of the document is not set, it will be loaded from the
        database.

        @param document: Document to be saved.
        @type document: Subclass of L{feat.agents.document.Document}
        @returns: Deferred called with the updated Document (id and revision
                  set)
        '''

    def get_document(document_id):
        '''
        Download the document from the database and instantiate it.
        The document should have the 'document_type' basing on which we decide
        which subclass of L{feat.agents.document.Document} to instantiate.

        @param document_id: The id of the document in the database.
        @returns: The Deffered called with the instance representing downloaded
                  document.
        '''

    def reload_document(document):
        '''
        Fetch the latest revision of the document and update it.

        @param document: Document to update.
        @type document: Subclass of L{feat.agents.document.Document}.
        @returns: Deferred called with the updated instance.
        '''

    def delete_document(document):
        '''
        Marks the document in the database as deleted. The document
        returns in the deferred can still be used in the application.
        For example one can call save_document on it to bring it back.

        @param document: Document to be deleted.
        @type document: Subclass of L{feat.agents.document.Document}.
        @returns: Deferred called with the updated document (latest revision).
        '''


class IAgent(Interface):
    '''Agent interface. It uses the L{IAgencyAgent} given at initialization
    time in order to perform its task.'''

    def initiate():
        '''Called after the agent is registered to an agency.'''
