import os
import shutil
import uuid
from asyncio import sleep
from ensurepip import version
from json.decoder import JSONDecodeError
from logging import getLogger
from os import getcwd, path, remove
from localplatform import chmod, service_restart, ON_LINUX, get_keep_systemd_service

from aiohttp import ClientSession, web

import helpers
from settings import SettingsManager

logger = getLogger("Updater")

class Updater:
    def __init__(self, context) -> None:
        self.context = context
        self.settings = self.context.settings
        # Exposes updater methods to frontend
        self.updater_methods = {
            "get_branch": self._get_branch,
            "get_version": self.get_version,
            "do_update": self.do_update,
            "do_restart": self.do_restart,
            "check_for_updates": self.check_for_updates
        }
        self.remoteVer = None
        self.allRemoteVers = None
        self.localVer = helpers.get_loader_version()

        try:
            self.currentBranch = self.get_branch(self.context.settings)
        except:
            self.currentBranch = 0
            logger.error("Current branch could not be determined, defaulting to \"Stable\"")

        if context:
            context.web_app.add_routes([
                web.post("/updater/{method_name}", self._handle_server_method_call)
            ])
            context.loop.create_task(self.version_reloader())

    async def _handle_server_method_call(self, request):
        method_name = request.match_info["method_name"]
        try:
            args = await request.json()
        except JSONDecodeError:
            args = {}
        res = {}
        try:
            r = await self.updater_methods[method_name](**args)
            res["result"] = r
            res["success"] = True
        except Exception as e:
            res["result"] = str(e)
            res["success"] = False
        return web.json_response(res)

    def get_branch(self, manager: SettingsManager):
        ver = manager.getSetting("branch", -1)
        logger.debug("current branch: %i" % ver)
        if ver == -1:
            logger.info("Current branch is not set, determining branch from version...")
            if self.localVer.startswith("v") and "-pre" in self.localVer:
                logger.info("Current version determined to be pre-release")
                return 1
            else:
                logger.info("Current version determined to be stable")
                return 0
        return ver

    async def _get_branch(self, manager: SettingsManager):
        return self.get_branch(manager)

    # retrieve relevant service file's url for each branch
    def get_service_url(self):
        logger.debug("Getting service URL")
        branch = self.get_branch(self.context.settings)
        match branch:
            case 0:
                url = "https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/unofficial_plugin_loader-release.service"
            case 1 | 2:
                url = "https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/unofficial_plugin_loader-prerelease.service"
            case _:
                logger.error("You have an invalid branch set... Defaulting to prerelease service, please send the logs to the devs!")
                url = "https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/unofficial_plugin_loader-prerelease.service"
        return str(url)

    async def get_version(self):
        return {
            "current": self.localVer,
            "remote": self.remoteVer,
            "all": self.allRemoteVers,
            "updatable": self.localVer != "unknown"
        }

    async def check_for_updates(self):
        logger.debug("checking for updates")
        selectedBranch = self.get_branch(self.context.settings)
        async with ClientSession() as web:
            async with web.request("GET", "https://api.github.com/repos/aarron-lee/decky-loader/releases", ssl=helpers.get_ssl_context()) as res:
                remoteVersions = await res.json()
                if selectedBranch == 0:
                    logger.debug("release type: release")
                    remoteVersions = list(filter(lambda ver: ver["tag_name"].startswith("v") and not ver["prerelease"] and not ver["tag_name"].find("-pre") > 0 and ver["tag_name"], remoteVersions))
                elif selectedBranch == 1:
                    logger.debug("release type: pre-release")
                    remoteVersions = list(filter(lambda ver:ver["tag_name"].startswith("v"), remoteVersions))
                else:
                    logger.error("release type: NOT FOUND")
                    raise ValueError("no valid branch found")
        self.allRemoteVers = remoteVersions
        logger.debug("determining release type to find, branch is %i" % selectedBranch)
        if selectedBranch == 0:
            logger.debug("release type: release")
            self.remoteVer = next(filter(lambda ver: ver["tag_name"].startswith("v") and not ver["prerelease"] and not ver["tag_name"].find("-pre") > 0 and ver["tag_name"], remoteVersions), None)
        elif selectedBranch == 1:
            logger.debug("release type: pre-release")
            self.remoteVer = next(filter(lambda ver:ver["tag_name"].startswith("v"), remoteVersions), None)
        else:
            logger.error("release type: NOT FOUND")
            raise ValueError("no valid branch found")
        logger.info("Updated remote version information")
        return await self.get_version()

    async def version_reloader(self):
        await sleep(30)
        while True:
            try:
                await self.check_for_updates()
            except:
                pass
            await sleep(60 * 60 * 6) # 6 hours

    async def do_update(self):
        logger.debug("do update.")
        
    async def do_restart(self):
        await service_restart("plugin_loader")
