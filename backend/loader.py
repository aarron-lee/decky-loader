from asyncio import Queue, sleep
from json.decoder import JSONDecodeError
from logging import getLogger
from os import listdir, path
from pathlib import Path
from traceback import print_exc

from aiohttp import web
from os.path import exists
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

from plugin import PluginWrapper

class FileChangeHandler(RegexMatchingEventHandler):
    def __init__(self, queue, plugin_path) -> None:
        super().__init__(regexes=[r'^.*?dist\/index\.js$', r'^.*?main\.py$'])
        self.logger = getLogger("file-watcher")
        self.plugin_path = plugin_path
        self.queue = queue
        self.disabled = True

    def maybe_reload(self, src_path):
        if self.disabled:
            return
        plugin_dir = Path(path.relpath(src_path, self.plugin_path)).parts[0]
        if exists(path.join(self.plugin_path, plugin_dir, "plugin.json")):
            self.queue.put_nowait((path.join(self.plugin_path, plugin_dir, "main.py"), plugin_dir, True))

    def on_created(self, event):
        src_path = event.src_path
        if "__pycache__" in src_path:
            return

        # check to make sure this isn't a directory
        if path.isdir(src_path):
            return

        # get the directory name of the plugin so that we can find its "main.py" and reload it; the
        # file that changed is not necessarily the one that needs to be reloaded
        self.logger.debug(f"file created: {src_path}")
        self.maybe_reload(src_path)

    def on_modified(self, event):
        src_path = event.src_path
        if "__pycache__" in src_path:
            return

        # check to make sure this isn't a directory
        if path.isdir(src_path):
            return

        # get the directory name of the plugin so that we can find its "main.py" and reload it; the
        # file that changed is not necessarily the one that needs to be reloaded
        self.logger.debug(f"file modified: {src_path}")
        self.maybe_reload(src_path)

class Loader:
    def __init__(self, server_instance, plugin_path, loop, live_reload=False) -> None:
        self.loop = loop
        self.logger = getLogger("Loader")
        self.plugin_path = plugin_path
        self.logger.info(f"plugin_path: {self.plugin_path}")
        self.plugins = {}
        self.watcher = None
        self.live_reload = live_reload

        if live_reload:
            self.reload_queue = Queue()
            self.observer = Observer()
            self.watcher = FileChangeHandler(self.reload_queue, plugin_path)
            self.observer.schedule(self.watcher, self.plugin_path, recursive=True)
            self.observer.start()
            self.loop.create_task(self.handle_reloads())
            self.loop.create_task(self.enable_reload_wait())

        server_instance.add_routes([
            web.get("/plugins", self.get_plugins),
            web.post("/plugins/{plugin_name}/methods/{method_name}", self.handle_plugin_method_call),
        ])

    async def enable_reload_wait(self):
        if self.live_reload:
            await sleep(10)
            self.logger.info("Hot reload enabled")
            self.watcher.disabled = False

    async def get_plugins(self, request):
        plugins = list(self.plugins.values())
        return web.json_response([{"name": str(i) if not i.legacy else "$LEGACY_"+str(i), "version": i.version} for i in plugins])

    def import_plugin(self, file, plugin_directory, refresh=False, batch=False):
        try:
            plugin = PluginWrapper(file, plugin_directory, self.plugin_path)
            if plugin.name in self.plugins:
                    if not "debug" in plugin.flags and refresh:
                        self.logger.info(f"Plugin {plugin.name} is already loaded and has requested to not be re-loaded")
                        return
                    else:
                        self.plugins[plugin.name].stop()
                        self.plugins.pop(plugin.name, None)
            if plugin.passive:
                self.logger.info(f"Plugin {plugin.name} is passive")
            self.plugins[plugin.name] = plugin.start()
            self.logger.info(f"Loaded {plugin.name}")
        except Exception as e:
            self.logger.error(f"Could not load {file}. {e}")
            print_exc()

    def import_plugins(self):
        self.logger.info(f"import plugins from {self.plugin_path}")

        directories = [i for i in listdir(self.plugin_path) if path.isdir(path.join(self.plugin_path, i)) and path.isfile(path.join(self.plugin_path, i, "plugin.json"))]
        for directory in directories:
            self.logger.info(f"found plugin: {directory}")
            self.import_plugin(path.join(self.plugin_path, directory, "main.py"), directory, False, True)

    async def handle_reloads(self):
        while True:
            args = await self.reload_queue.get()
            self.import_plugin(*args)

    async def handle_plugin_method_call(self, request):
        res = {}
        plugin = self.plugins[request.match_info["plugin_name"]]
        method_name = request.match_info["method_name"]
        try:
            method_info = await request.json()
            args = method_info["args"]
        except JSONDecodeError:
            args = {}
        try:
          if method_name.startswith("_"):
              raise RuntimeError("Tried to call private method")
          res["result"] = await plugin.execute_method(method_name, args)
          res["success"] = True
        except Exception as e:
            res["result"] = str(e)
            res["success"] = False
        return web.json_response(res)
