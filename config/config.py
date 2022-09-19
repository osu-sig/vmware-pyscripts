import configparser
import os

config = configparser.ConfigParser()

class GlobalConfig:
    def __init__(self):
        # load config from file
        config.read('vmware-pyscripts.conf')
        self.VSPHERE_HOST = config.get('main', 'VSphereHost')
        self.VSPHERE_PORT = config.get('main', 'VSpherePort')
        self.VSPHERE_VERIFY_SSL = config.getboolean('main', 'VSphereVerifySSL')
        self.IS_DEBUG = config.getboolean('main', 'EnableDebugging')
        self.LOG_DIR = config.get('logging', 'LogDir')
        self.TIMEZONE = config.get('logging', 'Timezone')
        self.VSPHERE_USERNAME = os.getenv('VSPHERE_USERNAME')
        self.VSPHERE_PASSWORD = os.getenv('VSPHERE_PASSWORD')
