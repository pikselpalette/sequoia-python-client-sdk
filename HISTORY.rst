*******
History
*******

1.0.0
=====

* First release.


1.1.0 (2017-10-25)
==================

* Upgrade to Python 3.6


1.2.0 (2019-03-06)
==================

* Libraries `urllib3` and `requests` upgraded to solve security issues:
    - `CVE-2018-20060 <https://nvd.nist.gov/vuln/detail/CVE-2018-20060>`_
    - `CVE-2018-18074 <https://nvd.nist.gov/vuln/detail/CVE-2018-18074>`_

1.2.1 (2019-03-26)
==================

* Load yaml config file for testing in a safer way as specified in `PyYAML <https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation>`_

2.0.0 (2019-06-06)
==================

* Removing python 2.7 compatibility

* Adding backoff to http requests. Configurable backoff from client creation

* Libraries `urllib3` and `requests` upgraded to solve security issues

2.1.0 (2019-09-30)
==================

* Modifying setup.cfg to allow different version formats (i.e development versions)
* Paging with `continue` parameter
* When token is expired, it is updated automatically with CLIENT_GRANT auth type

2.1.1 (2019-10-02)
==================
* Token fetching not restarting backoff. Retries continuing its count instead of restarting it when there is a invalid token

2.2.0 (2020-08-13)
==================
* Allowing to provide `correlation_id` value when the client is created
* Caching tokens by `grant_client_id` and `token_url` to avoid calling identity in case credentials are cached
* PageBrowser keeping a response cache to avoid duplicated requests
* Bug fixed when paging main content. Query params should to be added to next url
* New `AuthType.MUTUAL`

3.0.0 (2020-10-06)
==================
* Removing `transaction_id` value when the client is created
* Allowing to provide `user_id` and `application_id` values as correlation id prefix

4.0.0 (2020-10-21)
==================
* Python 3.5 support removed
* Python 3.7 supported
* Python 3.8 supported
* Pagination with `continue` parameter over linked resources supported
* Requirements upgraded

4.0.1 (2020-12-22)
==================
* When token is expired, it is updated automatically with CLIENT_GRANT auth type,
    the 401 response wasn't managed to do so, only the exception was.
    Now the 401 response is treated like that.

4.0.2 (2021-03-04)
==================
* Two new methods added to Criterion object so the fluent API is easier to use: `add_inclusion` and `add_criterion`.
