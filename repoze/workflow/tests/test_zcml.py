import unittest
from zope.testing.cleanup import cleanUp

class TestWorkflowDirective(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import WorkflowDirective
        return WorkflowDirective

    def _makeOne(self, context=None, name=None, state_attr=None,
                 initial_state=None, content_type=None):
        if context is None:
            context = DummyContext()
        return self._getTargetClass()(context, name, state_attr, initial_state,
                                      content_type)

    def test_ctor_with_state_attr(self):
        workflow = self._makeOne(name='public', state_attr='public2')
        self.assertEqual(workflow.state_attr, 'public2')
        
    def test_ctor_no_state_attr(self):
        workflow = self._makeOne(name='public')
        self.assertEqual(workflow.state_attr, 'public')

    def test_after(self):
        import types
        from zope.interface import Interface
        from zope.component import getSiteManager
        from repoze.workflow.interfaces import IWorkflow
        from repoze.workflow.workflow import Workflow
        from repoze.workflow.workflow import IWorkflowList
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_type=IDummy)
        directive.states = [ DummyState('private', a=1),
                             DummyState('public', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_private'),
                                  ]
        directive.after()
        actions = directive.context.actions
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action[0], (IWorkflow, IDummy, None, ''))
        callback = action[1]
        self.assertEqual(type(callback), types.FunctionType)
        callback()
        sm = getSiteManager()
        wflist = sm.adapters.lookup((IDummy,), IWorkflowList, name="")
        self.assertEqual(len(wflist), 1)
        wf_dict = wflist[0]
        self.assertEqual(wf_dict['elector'], None)
        self.assertEqual(wf_dict['workflow'].__class__, Workflow)
        workflow = wf_dict['workflow']
        self.assertEqual(
            workflow._transition_data,
            {'make_public':
             {'from_state': 'private', 'callback': None,
              'name': 'make_public', 'to_state': 'public',
              'permission':None},
             'make_private':
             {'from_state': 'private', 'callback': None,
              'name': 'make_private', 'to_state': 'public',
              'permission':None},
             }
            )
        self.assertEqual(workflow.initial_state, 'public')
        

    def test_after_raises_error_during_transition_add(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_type=IDummy)
        directive.states = [ DummyState('s1', a=1), DummyState('s2', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_public'),
                                  ]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action[1]
        self.assertRaises(ConfigurationError, callback)

    def test_after_raises_error_during_state_add(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_type=IDummy)
        directive.states = [ DummyState('public', a=1),
                             DummyState('public', b=2) ]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action[1]
        self.assertRaises(ConfigurationError, callback)

    def test_after_raises_error_during_check(self):
        from zope.interface import Interface
        from zope.configuration.exceptions import ConfigurationError
        class IDummy(Interface):
            pass
        directive = self._makeOne(initial_state='public',
                                  content_type=IDummy)
        directive.states = [ DummyState('only', a=1)]
        directive.after()
        actions = directive.context.actions
        action = actions[0]
        callback = action[1]
        self.assertRaises(ConfigurationError, callback)

class TestTransitionDirective(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import TransitionDirective
        return TransitionDirective

    def _makeOne(self, context=None, name=None, from_state=None,
                 to_state=None, callback=None, permission=None):
        return self._getTargetClass()(context, name, from_state,
                                      to_state, callback, permission)

    def test_ctor(self):
        directive = self._makeOne('context', 'name', 'from_state',
                                  'to_state', 'callback', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, 'from_state')
        self.assertEqual(directive.to_state, 'to_state')
        self.assertEqual(directive.permission, 'permission')
        self.assertEqual(directive.extras, {})

    def test_after(self):
        context = DummyContext(transitions=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.transitions, [directive])

class TestStateDirective(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from repoze.workflow.zcml import StateDirective
        return StateDirective

    def _makeOne(self, context=None, name=None):
        return self._getTargetClass()(context, name)

    def test_ctor(self):
        directive = self._makeOne('context', 'name')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')

    def test_after(self):
        context = DummyContext(states=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.states, [directive])

class TestKeyValuePair(unittest.TestCase):
    def _callFUT(self, context, key, value):
        from repoze.workflow.zcml import key_value_pair
        key_value_pair(context, key, value)

    def test_it_no_extras(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'key', 'value')
        self.assertEqual(context.context.extras, {'key':'value'})

class TestAlias(unittest.TestCase):
    def _callFUT(self, context, name):
        from repoze.workflow.zcml import alias
        alias(context, name)

    def test_it(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'thename')
        self.assertEqual(context.context.aliases, ['thename'])

class TestFixtureApp(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def test_execute_actions(self):
        from repoze.workflow.interfaces import IWorkflowList
        from repoze.workflow.workflow import Workflow
        from repoze.workflow.tests.fixtures.dummy import callback
        import repoze.workflow.tests.fixtures as package
        from repoze.workflow.tests.fixtures.dummy import IContent
        from repoze.workflow.tests.fixtures.dummy import elector
        from repoze.workflow.tests.fixtures.dummy import has_permission
        from zope.configuration import xmlconfig
        from zope.component import getSiteManager
        xmlconfig.file('configure.zcml', package, execute=True)
        sm = getSiteManager()
        wf_list = sm.adapters.lookup((IContent,),
                                     IWorkflowList, name='workflow')
        self.assertEqual(len(wf_list), 1)
        workflow_data = wf_list[0]
        self.assertEqual(workflow_data['elector'], elector)
        workflow = workflow_data['workflow']
        self.assertEqual(workflow.__class__, Workflow)
        self.assertEqual(workflow.title, 'the workflow')
        self.assertEqual(workflow.description, 'The workflow which is of the '
                         'testing fixtures package')
        self.assertEqual(workflow.permission_checker, has_permission)
        self.assertEqual(
            workflow._state_order,
            ['private', 'public'],
            )
        self.assertEqual(
            workflow._state_aliases,
            {'supersecret':'private'},
            )
        self.assertEqual(
            workflow._state_data,
            {u'public': {'callback':callback,
                         'description': u'Everybody can see it',
                         'title': u'Public'},
             u'private': {'callback':callback,
                          'description': u'Nobody can see it',
                          'title': u'Private'}},
            )
        transitions = workflow._transition_data
        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions['private_to_public'],
            {'from_state': u'private', 'callback': callback,
             'name': u'private_to_public', 'to_state': u'public',
             'permission':'moderate'}),
        self.assertEqual(transitions['public_to_private'],
             {'from_state': u'public', 'callback': callback,
              'name': 'public_to_private', 'to_state': u'private',
              'permission':'moderate',}
            )

class DummyContext:
    info = None
    def __init__(self, **kw):
        self.actions = []
        self.__dict__.update(kw)

class DummyState:
    def __init__(self, name, title=None, callback=None, aliases=(), **extras):
        self.name = name
        self.callback = callback
        self.extras = extras
        self.aliases = aliases
        
class DummyTransition:
    def __init__(self, name, from_state='private', to_state='public',
                 callback=None, permission=None, **extras):
        self.name = name
        self.from_state = from_state
        self.to_state = to_state
        self.callback = callback
        self.permission = permission
        self.extras = extras

                  
