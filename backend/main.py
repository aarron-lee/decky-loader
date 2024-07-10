# Change PyInstaller files permissions
import sys
from localplatform import (chmod, chown, service_stop, service_start,
                            ON_WINDOWS, get_log_level, get_live_reload, 
                            get_server_port, get_server_host, get_chown_plugin_path,
                            get_unprivileged_user, get_unprivileged_path, 
                            get_privileged_path)
if hasattr(sys, '_MEIPASS'):
    chmod(sys._MEIPASS, 755)
# Full imports
from asyncio import new_event_loop, set_event_loop, sleep
from json import dumps, loads
from logging import DEBUG, INFO, basicConfig, getLogger
from os import getenv, path
from traceback import format_exc
import multiprocessing

import aiohttp_cors
# Partial imports
from aiohttp import client_exceptions, WSMsgType
from aiohttp.web import Application, Response, get, run_app, static
from aiohttp_jinja2 import setup as jinja_setup

# local modules
from helpers import (REMOTE_DEBUGGER_UNIT, csrf_middleware, get_csrf_token,
                     mkdir_as_user, get_system_pythonpaths)
                     
from loader import Loader
from settings import SettingsManager
from utilities import Utilities
from customtypes import UserType


basicConfig(
    level=get_log_level(),
    format="[%(module)s][%(levelname)s]: %(message)s"
)

logger = getLogger("Main")
plugin_path = path.join(get_privileged_path(), "plugins")

def chown_plugin_dir():
    if not path.exists(plugin_path): # For safety, create the folder before attempting to do anything with it
        mkdir_as_user(plugin_path)

    if not chown(plugin_path, UserType.HOST_USER) or not chmod(plugin_path, 555):
        logger.error(f"chown/chmod exited with a non-zero exit code")

if get_chown_plugin_path() == True:
    chown_plugin_dir()

class PluginManager:
    def __init__(self, loop) -> None:
        self.loop = loop
        self.web_app = Application()
        self.web_app.middlewares.append(csrf_middleware)
        self.cors = aiohttp_cors.setup(self.web_app, defaults={
            "https://steamloopback.host": aiohttp_cors.ResourceOptions(
                expose_headers="*",
                allow_headers="*",
                allow_credentials=True
            )
        })
        self.plugin_loader = Loader(self.web_app, plugin_path, self.loop, get_live_reload())
        self.settings = SettingsManager("loader", path.join(get_privileged_path(), "settings"))
        self.utilities = Utilities(self)

        jinja_setup(self.web_app)

        async def startup(_):
            self.loop.create_task(self.load_plugins())

        self.web_app.on_startup.append(startup)

        self.loop.set_exception_handler(self.exception_handler)
        self.web_app.add_routes([get("/auth/token", self.get_auth_token)])

        for route in list(self.web_app.router.routes()):
            self.cors.add(route)
        self.web_app.add_routes([static("/static", path.join(path.dirname(__file__), 'static'))])
        self.web_app.add_routes([static("/legacy", path.join(path.dirname(__file__), 'legacy'))])

    def exception_handler(self, loop, context):
        if context["message"] == "Unclosed connection":
            return
        loop.default_exception_handler(context)

    async def get_auth_token(self, request):
        return Response(text=get_csrf_token())

    async def load_plugins(self):
        # await self.wait_for_server()
        logger.debug("Loading plugins")
        self.plugin_loader.import_plugins()
        if self.settings.getSetting("pluginOrder", None) == None:
          self.settings.setSetting("pluginOrder", list(self.plugin_loader.plugins.keys()))
          logger.debug("Did not find pluginOrder setting, set it to default")

    def run(self):
        return run_app(self.web_app, host=get_server_host(), port=get_server_port(), loop=self.loop, access_log=None)

if __name__ == "__main__":
    if ON_WINDOWS:
        # Fix windows/flask not recognising that .js means 'application/javascript'
        import mimetypes
        mimetypes.add_type('application/javascript', '.js')

        # Required for multiprocessing support in frozen files
        multiprocessing.freeze_support()

    # Append the loader's plugin path to the recognized python paths
    sys.path.append(path.join(path.dirname(__file__), "plugin"))

    # Append the system and user python paths
    sys.path.extend(get_system_pythonpaths())

    loop = new_event_loop()
    set_event_loop(loop)
    PluginManager(loop).run()
