# -*- coding: utf-8 -*-

from twisted.internet import defer
from synapse.api.constants import LoginType

import xmlrpclib
import logging

__version__ = "0.2.0"

logger = logging.getLogger(__name__)


class SpringRTSAuthProvider(object):
    __version__ = "0.2"

    def __init__(self, config, account_handler):

        self.log = logger

        self.account_handler = account_handler
        self.auth_handler = self.account_handler._auth_handler

        self.xmlrpc_uri = config.uri
        self.proxy = xmlrpclib.ServerProxy(self.xmlrpc_uri)
        self.account_info = None

    @staticmethod
    def get_supported_login_types():
        return {LoginType.PASSWORD: ("password",)}

    @defer.inlineCallbacks
    def check_auth(self, user_id, login_type, login_dict):

        self.log.debug("got password login for username {}".format(user_id))
        self.log.debug(login_dict)

        password = login_dict["password"]

        if not password:
            defer.returnValue(False)

        self.log.debug("Got password check for {}".format(user_id))

        # localpart = user_id.split(":", 1)[0][1:]
        localpart = user_id

        # get user info from uberserver

        self.account_info = self.proxy.get_account_info(localpart, password)

        auth = self.account_info.get("status")
        username = self.account_info.get("username")
        accountid = self.account_info.get("accountid")
        matrix_id = "{}_{}".format("id", accountid)

        if auth:
            self.log.debug("User not authenticated")
            yield defer.returnValue(None)

        self.log.debug("User {} authenticated".format(username))

        registration = False

        matrix_account = "@{}:{}".format(matrix_id, self.account_handler.hs.hostname)

        if not (yield self.account_handler.check_user_exists(matrix_account)):

            self.log.debug("User {} does not exist yet, creating...".format(matrix_account))

            matrix_account, access_token = (yield self.account_handler.register(localpart=matrix_id))

            store = yield self.account_handler.hs.get_profile_handler().store
            yield store.set_profile_displayname(matrix_account, username)

            registration = True

            self.log.debug("Registration based on XMLRPC data was successful for {}".format(matrix_account))

        else:

            self.log.debug("User {} already exists, registration skipped".format(matrix_account))

        yield defer.returnValue(matrix_account)

    @staticmethod
    def parse_config(config):
        class _XMLRPCConfig(object):
            pass

        xmlrpc_config = _XMLRPCConfig()

        xmlrpc_config.enabled = config.get("enabled", False)

        # verify config sanity
        _require_keys(config, [
            "uri",
        ])

        xmlrpc_config.uri = config["uri"]
        xmlrpc_config.user_id = ""
        xmlrpc_config.password = ""

        return xmlrpc_config


def _require_keys(config, required):
    missing = [key for key in required if key not in config]
    if missing:
        raise Exception(
            "XMLRPC enabled but missing required config values: {}".format(
                ", ".join(missing)
            )
        )
