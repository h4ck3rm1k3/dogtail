"""
Dogtail's procedural UI
All the classes here are intended to be single-instance, except for Action.
"""
__author__ = 'Zack Cerza <zcerza@redhat.com>'
##############################################################################
#                                                                            #
# WARNING: Here There Be Dragons (TM)                                        #
#                                                                            #
# If you don't understand how to use this API, you almost certainly don't    #
# want to read the code first. We make use of some very non-intuitive        #
# features of Python in order to make the API very simplistic. Therefore,    #
# you should probably only read this code if you're already familiar with    #
# some of Python's advanced features. You have been warned. ;)               #
#                                                                            #
##############################################################################

import tree
from predicate import GenericPredicate, IsADialogNamed, IsAnApplicationNamed
from config import config
import rawinput

#FocusError = "FocusError: %s not found"
class FocusError(Exception):
    pass

import errors
def focusFailed(type, name):
    if type is None or type == '':
        type = "widget"
    errors.warn('The requested %s \'%s\' could not be focused.' % (type, name))

ENOARGS = "At least one argument is needed"

class FocusBase:
    """
    The base for every class in the module. Does nothing special, really.
    """
    node = None

    def __getattr__ (self, name):
        # Fold all the Node's AT-SPI properties into the Focus object.
        try: return getattr(self.node, name)
        except AttributeError: 
            raise AttributeError, name

    def __setattr__ (self, name, value):
        # Fold all the Node's AT-SPI properties into the Focus object.
        if name == 'node':
            self.__dict__[name] = value
        else:
            try: setattr(self.node, name, value)
            except AttributeError: 
                raise AttributeError, name

class FocusApplication (FocusBase):
    """
    Keeps track of which application is currently focused.
    """
    desktop = tree.root
    def __call__ (self, name):
        """
        Search for an application that matches and refocus on the given name.
        """
        try:
            predicate = IsAnApplicationNamed(name)
            app = self.desktop.findChild(predicate, recursive = False, retry = False)
        except tree.SearchError, desc:
            if config.fatalErrors: raise FocusError, name
            else:
                focusFailed('Application', name)
                return False
        if app: 
            FocusApplication.node = app
            FocusDialog.node = None
            FocusWidget.node = None
        return True

class FocusDesktop (FocusBase):
    """
    This isn't used yet, and may never be used.
    """
    pass

class FocusDialog (FocusBase):
    """
    Keeps track of which dialog is currently focused.
    """
    def __call__ (self, name):
        """
        Search for a dialog that matches the given name and refocus on it.
        """
        result = None
        predicate = IsADialogNamed(name)
        try:
            result = FocusApplication.node.findChild(predicate, requireResult=False, recursive = False)
        except AttributeError: pass
        if result:
            FocusDialog.node = result
            FocusWidget.node = None
        else: 
            if config.fatalErrors: raise FocusError, predicate.debugName
            else:
                focusFailed('Dialog', name)
                return False
        return True

class FocusWidget (FocusBase):
    """
    Keeps track of which widget is currently focused.
    """
    def __call__ (self, name = '', roleName = '', description = ''):
        """
        If name, roleName or description are specified, search for a widget that matches and refocus on it.
        """
        if not name and not roleName and not description:
            raise TypeError, ENOARGS

        # search for a widget.
        result = None
        predicate = GenericPredicate(name = name, roleName = roleName, description = description)
        try:
            result = FocusWidget.node.findChild(predicate, requireResult = False, retry = False)
        except AttributeError: pass
        if result: FocusWidget.node = result
        else:
            try:
                result = FocusDialog.node.findChild(predicate, requireResult = False, retry = False)
            except AttributeError: pass
        if result: FocusWidget.node = result
        else:
            try:
                result = FocusApplication.node.findChild(predicate, requireResult = False, retry = False)
                if result: FocusWidget.node = result
            except AttributeError: 
                if config.fatalErrors: raise FocusError, name
                else:
                    focusFailed(roleName, name)
                    return False

        if result == None:
            FocusWidget.node = result
            if config.fatalErrors: raise FocusError, predicate.debugName
            else:
                focusFailed(roleName, name)
                return False
        return True

class Focus (FocusBase):
    """
    The container class for the focused application, dialog and widget.
    """

    def __getattr__ (self, name):
        raise AttributeError, name
    def __setattr__(self, name, value):
        if name in ('application', 'dialog', 'widget'):
            self.__dict__[name] = value
        else:
            raise AttributeError, name

    desktop = tree.root
    application = FocusApplication()
    app = application # shortcut :)
    dialog = FocusDialog()
    widget = FocusWidget()

    def button (self, name):
        """
        A shortcut to self.widget(name, roleName = 'push button')
        """
        return self.widget(name = name, roleName = 'push button')

    def frame (self, name):
        """
        A shortcut to self.widget(name, roleName = 'frame')
        """
        return self.widget(name = name, roleName = 'frame')

    def icon (self, name):
        """
        A shortcut to self.widget(name, roleName = 'icon')
        """
        return self.widget(name = name, roleName = 'icon')

    def menu (self, name):
        """
        A shortcut to self.widget(name, roleName = 'menu')
        """
        return self.widget(name = name, roleName = 'menu')

    def menuItem (self, name):
        """
        A shortcut to self.widget(name, roleName = 'menu item')
        """
        return self.widget(name = name, roleName = 'menu item')

    def table (self, name = ''):
        """
        A shortcut to self.widget(name, roleName 'table')
        """
        return self.widget(name = name, roleName = 'table')

    def tableCell (self, name = ''):
        """
        A shortcut to self.widget(name, roleName 'table cell')
        """
        return self.widget(name = name, roleName = 'table cell')

    def text (self, name = ''):
        """
        A shortcut to self.widget(name, roleName = 'text')
        """
        return self.widget(name = name, roleName = 'text')

    def window (self, name):
        """
        A shortcut to self.widget(name, roleName = 'window')
        """
        return self.widget(name = name, roleName = 'window')

class Action (FocusWidget):
    """
    Aids in executing AT-SPI actions, refocusing the widget if necessary.
    """
    def __init__ (self, action):
        """
        action is a string with the same name as the AT-SPI action you wish to execute using this class.
        """
        self.action = action

    def __call__ (self, name = '', roleName = '', description = '', delay = config.actionDelay):
        """
        If name, roleName or description are specified, first search for a widget that matches and refocus on it.
        Then execute the action.
        """
        if name or roleName or description:
            FocusWidget.__call__(self, name = name, roleName = roleName, description = description)
        self.node.doAction(self.action)

    def __getattr__ (self, attr):
        return getattr(FocusWidget.node, attr)

    def __setattr__ (self, attr, value):
        if attr == 'action':
            self.__dict__[attr] = value
        else: setattr(FocusWidget, attr, value)

    def button (self, name):
        """
        A shortcut to self(name, roleName = 'push button')
        """
        self.__call__(name = name, roleName = 'push button')

    def menu (self, name):
        """
        A shortcut to self(name, roleName = 'menu')
        """
        self.__call__(name = name, roleName = 'menu')

    def menuItem (self, name):
        """
        A shortcut to self(name, roleName = 'menu item')
        """
        self.__call__(name = name, roleName = 'menu item')

    def table (self, name = ''):
        """
        A shortcut to self(name, roleName 'table')
        """
        self.__call__(name = name, roleName = 'table')

    def tableCell (self, name = ''):
        """
        A shortcut to self(name, roleName 'table cell')
        """
        self.__call__(name = name, roleName = 'table cell')

    def text (self, name = ''):
        """
        A shortcut to self(name, roleName = 'text')
        """
        self.__call__(name = name, roleName = 'text')

class Click (Action):
    """
    A special case of Action, Click will eventually handle raw mouse events.
    """
    primary = 1
    middle = 2
    secondary = 3
    def __init__ (self):
        Action.__init__(self, 'click')

    def __call__ (self, name = '', roleName = '', description = '', raw = True, button = primary, delay = config.actionDelay):
        """
        By default, execute a raw mouse event.
        If raw is False or if button evaluates to False, just pass the rest of 
        the arguments to Action.
        """
        if raw and button:
            # We're doing a raw mouse click
            FocusWidget.__call__(self, name = name, roleName = roleName, description = description)
            Click.node.click(button)
        else:
            Action.__call__(self, name = name, roleName = roleName, description = description, delay = delay)

class Select (Action):
    """
    Aids in selecting and deselecting widgets, i.e. page tabs
    """
    select = 'select'
    deselect = 'deselect'
    def __init__(self, action):
        """
        action must be 'select' or 'deselect'.
        """
        if action not in (self.select, self.deselect):
            raise ValueError, action
        Action.__init__(self, action)

    def __call__ (self, name = '', roleName = '', description = '', delay = config.actionDelay):
        """
        If name, roleName or description are specified, first search for a widget that matches and refocus on it.
        Then execute the action.
        """
        if name or roleName or description:
            FocusWidget.__call__(self, name = name, roleName = roleName, description = description)
        func = getattr(self.node, self.action)
        func()
        
def type(text):
    if focus.widget.node:
        focus.widget.node.typeText(text)
    else:
        rawinput.typeText(text)

def keyCombo(combo):
    if focus.widget.node:
        focus.widget.node.keyCombo(combo)
    else:
        rawinput.keyCombo(combo)

def run(application, arguments = '', appName = ''):
    from utils import run as utilsRun
    utilsRun(application + ' ' + arguments, appName = appName)
    focus.application(application)

focus = Focus()
click = Click()
activate = Action('activate')
openItem = Action('open')
menu = Action('menu')
select = Select(Select.select)
deselect = Select(Select.deselect)
