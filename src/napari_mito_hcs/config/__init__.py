""" Configuration objects and defaults

Example: Load an object from disk, change some attributes, write it back to disk

.. code-block:: python

    config = Configurable.load_config_file('path/to/file.toml')
    config.foo = 1
    config.bar = 2
    config.save_config_file('path/to/file.toml')

Attributes are assumed to be basic python types that can be serialized to/from `TOML <https://toml.io/en/>`_

.. note:: This framework assumes the arguments to ``__init__`` are the same as the public attributes of the class.

    Private attributes are not saved

Classes:

* :py:class:`Configurable`: Enable a pipeline class to be saved/loaded from disk

"""

# Imports
from typing import Union
import pathlib
from importlib import resources

# 3rd party
import tomlkit

# Classes


class Configurable(object):
    """ Base class for pipeline objects that can be saved/loaded from disk

    Alternative constructors:

    * :py:meth:`load_default`: Load the default config under this folder
    * :py:meth:`load_config_file`: Load a config file from disk
    * :py:meth:`load_config`: Load a config from a string

    Methods:

    * :py:meth:`save_config_file`: Save the current config file to disk
    * :py:meth:`save_config`: Save the current config to a string

    """

    def save_config_file(self, config_file: Union[str, pathlib.Path]):
        """ Write the class attributes to a file

        :param Path config_file:
            Path to the config file to write
        """
        if isinstance(config_file, str):
            config_file = pathlib.Path(config_file)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with config_file.open('wt') as fp:
            fp.write(self.save_config())

    def save_config(self) -> str:
        """ Write the class attributes to a string

        :returns:
            A TOML formatted string that represents this class
        """
        self_dict = {k: v for k, v in vars(self).items() if not k.startswith('_')}
        return tomlkit.dumps(self_dict)

    @classmethod
    def load_config_file(cls, config_file: Union[str, pathlib.Path]) -> 'Configurable':
        """ Load the class from a config file

        :param Path config_file:
            Path to the config file to write
        :returns:
            An instance of the class initialized with the parameters in the config
        """
        if isinstance(config_file, str):
            config_file = pathlib.Path(config_file)

        with config_file.open('rt') as fp:
            config_data = fp.read()
        return cls.load_config(config_data)

    @classmethod
    def load_config(cls, config: str) -> 'Configurable':
        """ Load the class from a config file

        :param str config:
            The TOML formatted config string for this class
        :returns:
            An instance of the class initialized with the parameters in the config
        """
        data = tomlkit.loads(config)
        return cls(**data)

    @classmethod
    def load_default(cls, config_name: str) -> 'Configurable':
        """ Load the class from a default config defined in this module

        :param str config_name:
            The name of the default config to load
        :returns:
            An instance of the class initialized with the parameters in the config
        """
        # Remove any path information
        config_name = pathlib.Path(config_name).name
        if not config_name.endswith('.toml'):
            config_name = config_name + '.toml'

        config_file = resources.files(__package__) / config_name
        return cls.load_config_file(config_file)
