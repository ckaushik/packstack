"""
Installs and configures ssh keys
"""

import glob
import logging
import os

from packstack.installer import processors
from packstack.installer import validators
from packstack.installer import utils

from packstack.modules.common import filtered_hosts

# Controller object will be initialized from main flow
controller = None

# Plugin name
PLUGIN_NAME = "OS-SSHKEYS"
PLUGIN_NAME_COLORED = utils.color_text(PLUGIN_NAME, 'blue')

logging.debug("plugin %s loaded", __name__)

def initConfig(controllerObject):
    global controller
    controller = controllerObject
    logging.debug("Adding SSH KEY configuration")
    paramsList = [
                  {"CMD_OPTION"      : "ssh-public-key",
                   "USAGE"           : "Path to a Public key to install on servers. If a usable key has not been installed on the remote servers the user will be prompted for a password and this key will be installed so the password will not be required again",
                   "PROMPT"          : "Enter the path to your ssh Public key to install on servers",
                   "OPTION_LIST"     : [],
                   "VALIDATORS"      : [validators.validate_file],
                   "PROCESSORS"      : [processors.process_ssh_key],
                   "DEFAULT_VALUE"   : (glob.glob(os.path.join(os.environ["HOME"], ".ssh/*.pub"))+[""])[0],
                   "MASK_INPUT"      : False,
                   "LOOSE_VALIDATION": False,
                   "CONF_NAME"       : "CONFIG_SSH_KEY",
                   "USE_DEFAULT"     : False,
                   "NEED_CONFIRM"    : False,
                   "CONDITION"       : False },
                 ]

    groupDict = { "GROUP_NAME"            : "SSHKEY",
                  "DESCRIPTION"           : "SSH Configs ",
                  "PRE_CONDITION"         : lambda x: 'yes',
                  "PRE_CONDITION_MATCH"   : "yes",
                  "POST_CONDITION"        : False,
                  "POST_CONDITION_MATCH"  : True}

    controller.addGroup(groupDict, paramsList)


def initSequences(controller):
    puppetsteps = [
             {'title': 'Setting up ssh keys',
              'functions':[installKeys]}
    ]
    controller.addSequence("Setting up ssh keys", [], [], puppetsteps)


def installKeys(config):
    with open(config["CONFIG_SSH_KEY"]) as fp:
        sshkeydata = fp.read().strip()
    for hostname in filtered_hosts(config):
        server = utils.ScriptRunner(hostname)
        # TODO replace all that with ssh-copy-id
        server.append("mkdir -p ~/.ssh")
        server.append("chmod 500 ~/.ssh")
        server.append("grep '%s' ~/.ssh/authorized_keys > /dev/null 2>&1 || echo %s >> ~/.ssh/authorized_keys" % (sshkeydata, sshkeydata))
        server.append("chmod 400 ~/.ssh/authorized_keys")
        server.append("restorecon -r ~/.ssh")
        server.execute()
