import os

import six
import yaml

from omegaml.client.userconf import get_omega_from_apikey
from omegaml.client.util import protected
from omegaml.omega import Omega as CoreOmega
from omegaml.runtimes import OmegaRuntime


class OmegaCloud(CoreOmega):
    """
    Client API to omegaml cloud

    Provides the following APIs:

    * :code:`datasets` - access to datasets stored in the cluster
    * :code:`models` - access to models stored in the cluster
    * :code:`runtimes` - access to the cluster compute resources
    * :code:`jobs` - access to jobs stored and executed in the cluster
    * :code:`scripts` - access to lambda modules stored and executed in the cluster

    """

    def __init__(self, auth=None, **kwargs):
        """
        Initialize the client API
        """
        super(OmegaCloud, self).__init__(**kwargs)
        self.auth = auth

    def _make_runtime(self, celeryconf):
        return OmegaCloudRuntime(self, bucket=self.bucket, defaults=self.defaults, celeryconf=celeryconf)

    def _clone(self, **kwargs):
        kwargs.update(auth=self.auth)
        return super()._clone(**kwargs)

    def __repr__(self):
        return 'OmegaCloud(bucket={}, auth={})'.format(self.bucket or 'default', repr(self.auth))


class OmegaCloudRuntime(OmegaRuntime):
    """
    omegaml hosted compute cluster gateway
    """

    def __init__(self, omega, **kwargs):
        super().__init__(omega, **kwargs)
        self._auth_kwarg = protected('auth')

    def __repr__(self):
        return 'OmegaCloudRuntime(auth={})'.format(repr(self.omega.auth))

    @property
    def _common_kwargs(self):
        common = super()._common_kwargs
        common['task'].update({self._auth_kwarg: self.auth_tuple})
        label = common['routing'].get('label', 'default')
        common['routing'].update(self.build_account_routing(label))
        return common

    @property
    def auth_tuple(self):
        auth = self.omega.auth
        return auth.userid, auth.apikey, auth.qualifier

    @property
    def dispatch_label(self):
        return self.omega.auth.userid

    def build_account_routing(self, label):
        # build the queue
        account_routing = {
            'label': '{self.dispatch_label}-{label}'.format(**locals())
        }
        return account_routing


def setup(userid=None, apikey=None, api_url=None, qualifier=None, bucket=None):
    # from now on, link OmegaCloud implementation as the default
    import omegaml as om
    api_url = api_url or os.environ.get('OMEGA_RESTAPI_URL') or 'https://hub.omegaml.io'
    om.Omega = OmegaCloud
    om.setup = setup
    om.get_omega_for_task = lambda *args, **kwargs: setup(*args, **kwargs)
    om = get_omega_from_apikey(userid, apikey, api_url=api_url, qualifier=qualifier, view=False)
    return om[bucket]


def setup_from_config(config_file=None):
    from omegaml import _base_config
    config_file = config_file or _base_config.OMEGA_CONFIG_FILE
    if isinstance(config_file, six.string_types) and os.path.exists(config_file):
        with open(config_file, 'r') as fin:
            userconfig = yaml.safe_load(fin)
            if isinstance(userconfig, dict) and 'OMEGA_USERID' in userconfig:
                try:
                    omega = setup(userid=userconfig['OMEGA_USERID'],
                                  apikey=userconfig['OMEGA_APIKEY'],
                                  api_url=userconfig['OMEGA_RESTAPI_URL'])
                except:
                    # TODO make this a SystemError so that OmegaDeferredIstance.setup reverts to proper defaults
                    raise ValueError('Could not login using config file {}'.format(config_file))
            else:
                _base_config.OMEGA_CONFIG_FILE = config_file
                raise SystemError
            return omega
    raise SystemError('Config file {} does not exist'.format(config_file))
