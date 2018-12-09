from typing import List

import wpilib
from networktables.util import ChooserControl

import logging

logger = logging.getLogger("marsutils")

__all__ = ["ControlManager", "ControlInterface", "with_ctrl_manager", "provide_setup"]


class ControlInterface:
    """
        ``ControlInterface`` is the base class that all interfaces must subclass to
        be used with :class:`.ControlManager`.

        You must define a ``_DISPLAY_NAME``. This value will be displayed in the dashboard chooser.
        Optionally, you can define a ``_SORT`` value. The larger the value, the higher priority
        it will be given in the chooser.
    """

    _DISPLAY_NAME: str
    _SORT = 0

    def teleopPeriodic(self):
        pass

    def enabled(self):
        pass

    def disabled(self):
        pass


class ControlManager:
    """
        This class manages creating a dashboard chooser and the periodic
        calling of a series of "control interface" components.

        Each control interface must subclass :class:`ControlInterface` and define ``_DISPLAY_NAME``.

        Once this has been initalized with the list of interfaces, you must manually call
        every event function you want your components to recive, like "teleopPeridic" and
        "teleopInit" and they will be forwarded to the active interface"
        
        You can optionally define a ``_SORT`` value for your interfaces.
        The larger the value, the higher priority it will be given in the chooser.
    """

    __slots__ = [
        "control_mode",
        "control_interfaces",
        "control_chooser",
        "control_chooser_control",
    ]

    def __init__(
        self, *interfaces: ControlInterface, dashboard_key: str = "Control Mode"
    ):
        assert len(interfaces) > 0, "No control interfaces given"

        # Sort the interfaces by their _SORT values
        interfaces = tuple(sorted(interfaces, key=lambda x: x._SORT, reverse=True))

        self.control_mode = None
        self.control_interfaces: List[ControlInterface] = []

        self.control_chooser = wpilib.SendableChooser()

        for i, mode in enumerate(interfaces):
            if not hasattr(mode, "_DISPLAY_NAME"):
                logger.error(
                    f'Control interface {mode.__class__.__name__} has no "_DISPLAY_NAME" attr, \
                    skipping'
                )
                continue
            if not isinstance(mode._DISPLAY_NAME, str):
                logger.error(
                    f'Control interface {mode.__class__.__name__} has non-string "_DISPLAY_NAME" \
                    attr'
                )
                continue
            self.control_interfaces.append(mode)
            # Make the first entry the default
            # TODO: Configurable?
            if i == 0:
                self.control_chooser.addDefault(mode._DISPLAY_NAME, i)
            else:
                self.control_chooser.addObject(mode._DISPLAY_NAME, i)

        wpilib.SmartDashboard.putData(dashboard_key, self.control_chooser)

        self.control_chooser_control = ChooserControl(
            dashboard_key, on_selected=self.control_mode_changed
        )

    def teleopPeriodic(self):
        if self.control_mode is not None:
            self.control_mode.teleopPeriodic()

    def control_mode_changed(self, new_value):
        new_selected: int = self.control_chooser.getSelected()
        if new_selected is None:
            return
        if new_selected >= len(self.control_interfaces):
            logger.error(f"Invalid control mode: {new_selected}")
            return
        if self.control_mode != self.control_interfaces[new_selected]:
            if self.control_mode is not None:
                self.control_mode.disabled()
            self.control_mode = self.control_interfaces[new_selected]
            if self.control_mode is not None:
                self.control_mode.enabled()


def with_ctrl_manager(klass):
    """
    A decorator to be used with ``MagicRobot`` robot classes which
    automatically processes :class:`ControlInterface` members

    Any :class:`ControlInterface` with a ``_DISPLAY_NAME`` variable
    defined will be added to a chooser on the dashboard and its associated
    methods will be automatically called
    """
    from robotpy_ext.misc.annotations import get_class_annotations

    def empty_execute(self):
        pass

    for m, ctyp in get_class_annotations(klass).items():
        if not hasattr(ctyp, "execute"):
            ctyp.execute = empty_execute

    def robotInit(_self):
        _self.__old_robotInit_ctrlmgnr()

        components = []
        for m in dir(_self):
            if m.startswith("_") or isinstance(getattr(type(_self), m, True), property):
                continue

            ctyp = getattr(_self, m, None)
            if ctyp is None:
                continue

            if not issubclass(ctyp.__class__, ControlInterface):
                continue

            components.append(ctyp)

        assert (
            len(components) > 0
        ), "No valid control components found. Do they subclass ControlInterface?"

        _self.__control_manager = ControlManager(*components)

    klass.__old_robotInit_ctrlmgnr = klass.robotInit
    klass.robotInit = robotInit

    def teleopPeriodic(_self):
        _self.__control_manager.teleopPeriodic()
        _self.__old_teleopPeriodic()

    klass.__old_teleopPeriodic = klass.teleopPeriodic
    klass.teleopPeriodic = teleopPeriodic

    return klass


def provide_setup(klass):
    """
        As the ``MagicRobot`` class uses the ``robotInit()`` method, this decorator
        provides ``MagicRobot`` classes with a ``setup()`` function that is called
        after the ``createObjects()`` function is called
    """

    def robotInitSetup(_self):
        _self.__old_robotInit_setup()

        if hasattr(klass, "setup"):
            _self.setup()
        else:
            logger.warning(
                "{} was wrapped with @provide_setup but no setup() function was found".format(
                    klass
                )
            )

    klass.__old_robotInit_setup = klass.robotInit
    klass.robotInit = robotInitSetup

    return klass
