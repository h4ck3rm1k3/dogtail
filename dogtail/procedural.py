"""
Dogtail's procedural UI
All the classes here are intended to be single-instance, except for Action.
"""
__author__ = 'Zack Cerza <zcerza@redhat.com>'

import tree
from predicate import GenericPredicate, IsADialogNamed
from config import config
from time import sleep

#FocusError = "FocusError: %s not found"
class FocusError(Exception):
    pass

ENOARGS = "At least one argument is needed"

class FocusBase:
    """
    The base for every class in the module. Does nothing special, really.
    """
    def __getattr__ (self, name):
        # Fold all the Node's AT-SPI properties into the Focus object.
        try: return getattr(self.node, name)
        except AttributeError: raise AttributeError, name

    def __setattr__ (self, name, value):
        # Fold all the Node's AT-SPI properties into the Focus object.
        if name == 'node':
            self.__dict__[name] = value
        else:
            try: setattr(self.node, name, value)
            except AttributeError: raise AttributeError, name

class FocusApplication (FocusBase):
    """
    Keeps track of which application is currently focused.
    """
    desktop = tree.root
    def __call__ (self, name = '', description = ''):
        """
        If name or description are specified, search for an application that matches and refocus on it.
        """
        if not name and not description:
            raise TypeError, ENOARGS
        # search for an application.
        matched = False
        for app in self.desktop.children:
            nameMatch = app.name == name
            descriptionMatch = app.description == description
            if nameMatch and descriptionMatch:
                FocusApplication.node = app
                FocusDialog.node = None
                FocusWidget.node = None
                matched = True
                break
        if not matched: raise FocusError, name

class FocusDesktop (FocusBase):
    """
    This isn't used yet, and may never be used.
    """
    pass

class FocusDialog (FocusBase):
    """
    Keeps track of which dialog is currently focused.
    """
    def __call__ (self, name = '', description = ''):
        """
        If name or description are specified, search for a dialog that matches and refocus on it.
        """
        if not name and not description:
            raise TypeError, ENOARGS
        result = None
        predicate = IsADialogNamed(name)
        try:
            result = FocusApplication.node.findChild(predicate, requireResult=False, recursive = False)
        except AttributeError: pass
        if result:
            FocusDialog.node = result
            FocusWidget.node = None
        else: raise FocusError, predicate.debugName

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
            except AttributeError: raise FocusError, name

        if result == None:
            FocusWidget.node = result
            raise FocusError, predicate.debugName

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
        self.widget(name = name, roleName = 'push button')

    def frame (self, name):
        """
        A shortcut to self.widget(name, roleName = 'frame')
        """
        self.widget(name = name, roleName = 'frame')

    def icon (self, name):
        """
        A shortcut to self.widget(name, roleName = 'icon')
        """
        self.widget(name = name, roleName = 'icon')

    def menu (self, name):
        """
        A shortcut to self.widget(name, roleName = 'menu')
        """
        self.widget(name = name, roleName = 'menu')

    def menuItem (self, name):
        """
        A shortcut to self.widget(name, roleName = 'menu item')
        """
        self.widget(name = name, roleName = 'menu item')

    def table (self, name = ''):
        """
        A shortcut to self.widget(name, roleName 'table')
        """
        self.widget(name = name, roleName = 'table')

    def tableCell (self, name = ''):
        """
        A shortcut to self.widget(name, roleName 'table cell')
        """
        self.widget(name = name, roleName = 'table cell')

    def text (self, name = ''):
        """
        A shortcut to self.widget(name, roleName = 'text')
        """
        self.widget(name = name, roleName = 'text')

    def window (self, name):
        """
        A shortcut to self.widget(name, roleName = 'window')
        """
        self.widget(name = name, roleName = 'window')

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
        sleep(delay)

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

    def __call__ (self, name = '', roleName = '', description = '', raw = False, button = primary, delay = config.actionDelay):
        """
        If coords or button are specified, execute a raw mouse event. If not, just pass the rest of the arguments to Action.
        """
        if raw and button:
            # We're doing a raw mouse click
            FocusWidget.__call__(self, name = name, roleName = roleName, description = description)
            Click.node.rawClick(button)
            sleep(delay)
        else:
            Action.__call__(self, name = name, roleName = roleName, description = description, delay = delay)

def run(application, arguments = '', appName = ''):
    from utils import run as utilsRun
    utilsRun(application + arguments, appName = appName)
    focus.application(application)


focus = Focus()
click = Click()
activate = Action('activate')
openItem = Action('open')
menu = Action('menu')
