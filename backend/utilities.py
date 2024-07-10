import uuid
import os
from json.decoder import JSONDecodeError
from traceback import format_exc

from asyncio import sleep, start_server, gather, open_connection
from aiohttp import ClientSession, web

from logging import getLogger
import helpers
import subprocess
from localplatform import service_stop, service_start

class Utilities:
    def __init__(self, context) -> None:
        self.context = context
        self.util_methods = {
            "ping": self.ping,
            "http_request": self.http_request,
            "install_plugin": self.install_plugin,
            "install_plugins": self.install_plugins,
            "cancel_plugin_install": self.cancel_plugin_install,
            "confirm_plugin_install": self.confirm_plugin_install,
            "uninstall_plugin": self.uninstall_plugin,
            "allow_remote_debugging": self.allow_remote_debugging,
            "disallow_remote_debugging": self.disallow_remote_debugging,
            "set_setting": self.set_setting,
            "get_setting": self.get_setting,
            "filepicker_ls": self.filepicker_ls,
        }

        self.logger = getLogger("Utilities")

        self.rdt_proxy_server = None
        self.rdt_script_id = None
        self.rdt_proxy_task = None

        if context:
            context.web_app.add_routes([
                web.post("/methods/{method_name}", self._handle_server_method_call)
            ])

    async def _handle_server_method_call(self, request):
        method_name = request.match_info["method_name"]
        try:
            args = await request.json()
        except JSONDecodeError:
            args = {}
        res = {}
        try:
            r = await self.util_methods[method_name](**args)
            res["result"] = r
            res["success"] = True
        except Exception as e:
            res["result"] = str(e)
            res["success"] = False
        return web.json_response(res)


    async def http_request(self, method="", url="", **kwargs):
        async with ClientSession() as web:
            res = await web.request(method, url, ssl=helpers.get_ssl_context(), **kwargs)
            text = await res.text()
        return {
            "status": res.status,
            "headers": dict(res.headers),
            "body": text
        }

    async def ping(self, **kwargs):
        return "pong"


    async def get_setting(self, key, default):
        return self.context.settings.getSetting(key, default)

    async def set_setting(self, key, value):
        return self.context.settings.setSetting(key, value)


