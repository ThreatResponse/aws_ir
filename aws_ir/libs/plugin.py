import aws_ir_plugins
import os


from functools import partial
from pluginbase import PluginBase


class Core(object):
    """Enumerates core plugins that are part of the AWS_IR offering."""
    def __init__(self):
        self.here = os.path.abspath(os.path.dirname(__file__))
        get_path = partial(os.path.join, self.here)

        self.plugin_base = PluginBase(
            package='aws_ir.plugins',
            searchpath=[os.path.dirname(aws_ir_plugins.__file__)]
        )

        self.source = self.plugin_base.make_plugin_source(
            searchpath=[os.path.dirname(aws_ir_plugins.__file__), get_path('~/.awsir/plugins')]
        )

        self.list = self.source.list_plugins()

    def key_plugins(self):
        """Return list of only the plugins that relate to the access key."""
        plugins = ""
        for p in self.list:
            if "_key" in p:
                if plugins == "":
                    plugins = p
                else:
                    plugins = plugins + ',' + p
        return plugins

    def instance_plugins(self):
        """Return list of only the plugins that relate to the instance compromise."""
        plugins = ""
        for p in self.list:
            if "_host" in p:
                if plugins == "":
                    plugins = p
                else:
                    plugins = plugins + ',' + p
        plugins = plugins + ',' + 'get_memory'
        return plugins


class Custom(object):
    """Enumerates core plugins that are part of the AWS_IR offering."""
    def __init__(self):
        self.plugin_base = PluginBase(
            package='aws_ir.plugins',
            searchpath=[(os.getenv("HOME") + '/.awsir/plugins')]
        )

        self.source = self.plugin_base.make_plugin_source(
            searchpath=[(os.getenv("HOME") + '/.awsir/plugins')]
        )

        self.list = self.source.list_plugins()
