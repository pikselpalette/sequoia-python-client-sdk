=======
History
=======

1.0.0
------------------

* First release.


1.1.0 (2017-10-25)
------------------

* Upgrade to Python 3.6


1.2.0 (2019-03-06)
------------------

* Libraries `urllib3` and `requests` upgraded to solve security issues:
    - `CVE-2018-20060 <https://nvd.nist.gov/vuln/detail/CVE-2018-20060>`_
    - `CVE-2018-18074 <https://nvd.nist.gov/vuln/detail/CVE-2018-18074>`_

1.2.1 (2019-03-26)
------------------

* Load yaml config file for testing in a safer way as specified in `PyYAML <https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation>`_

2.0.0 (2019-06-06)
------------------

* Removing python 2.7 compatibility

* Adding backoff to http requests. Configurable backoff from client creation

* Libraries `urllib3` and `requests` upgraded to solve security issues

2.1.0 (2019-09-30)
------------------

* Modifying setup.cfg to allow different version formats (i.e development versions)
* Paging with `continue` parameter
* When token is expired, it is updated automatically with CLIENT_GRANT auth type

2.1.1 (2019-10-02)
------------------
* Token fetching not restarting backoff. Retries continuing its count instead of restarting it when there is a invalid token
