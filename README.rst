.. image:: https://pikselgroup.com/broadcast/wp-content/uploads/sites/3/2017/09/P-P.png
    :target: https://piksel.com/product/piksel-palette/
    :align: center
    :alt: Piksel Palette

#########################
Python Sequoia Client SDK
#########################
A Python Client SDK for interacting with client services.

The central idea is that Client SDK allows python application code to communicate with the `Piksel Palette`_ RESTful RESTful services.
Users can also search, filter and select their response collections.

.. _Piksel Palette: http://developer.pikselpalette.com/

************
Installation
************

.. code-block:: bash

    pip install sequoia-client-sdk


*****
Usage
*****


Creating a SequoiaClient
========================

To create the client it is necessary to provide the url for the service ``registry`` and named arguments specifying the
credentials for the auth_type being used. If no auth_type is specified, then the default CLIENT_GRANT is used:

    .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        grant_client_id="clientId",
                        grant_client_secret="clientSecret")


Authentication types
====================

When creating the client, authentication type can be specified using the parameter ``auth_type``:

    .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        auth_type=AuthType.CLIENT_GRANT,
                        grant_client_id="clientId",
                        grant_client_secret="clientSecret")


The Sequoia RESTful services have an OAuth token-based authorisation model, meaning that the Client SDK must first
acquire a time-limited access token before making further requests. CLIENT_GRANT or BYO_TOKEN types should be used.

It is also possible to connect to the client via a proxy using two-way TLS authentication. In this case, MUTUAL
auth_type should be used.


There are four authentication types:

CLIENT_GRANT type
-----------------

This is the default type. With CLIENT_GRANT mode ``grant_client_id`` and ``grant_client_secret`` parameters are
used to get an access token. The access token is refreshed automatically when expired. Optionally, ``byo_token``
parameter can be provided when instantiating the client, and will be used until it is expired.
Then the access token is refreshed automatically.

    .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        auth_type=AuthType.CLIENT_GRANT,
                        grant_client_id="clientId",
                        grant_client_secret="clientSecret")


BYO_TOKEN type
--------------

With this method ``byo_token`` is required. That access token will be used to authenticate requests. The access token will
be used along the client life and won't be refreshed.


NO_AUTH type
------------

Mode used when no authentication is required.


MUTUAL type
------------

Mode used when mutual TLS authentication is required. Paths to local client certificate, client key and a server
certificate files must be provided in the client_cert, client_key and server_cert arguments respectively.

    .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        auth_type=AuthType.MUTUAL,
                        client_cert="/certs/client_cert.pem",
                        client_key="/certs/client_key.pem",
                        server_cert="/certs/server_cert.pem",
                        ...


Content Type
====================

By default the client sets "Content-Type" and "Accept' header values of http requests to  "application/vnd.piksel+json".
A different content type for these headers can be specified in the content_type parameter when creating a client.

 .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        auth_type=AuthType.MUTUAL,
                        client_cert="/certs/client_cert.pem",
                        client_key="/certs/client_key.pem",
                        server_cert="/certs/server_cert.pem",
                        content_type="application/json"
                        )


Creating an endpoint
====================

An endpoint defines the resource on which to perform the operations.

    .. code-block:: python

        profile_endpoint = client.workflow.profiles
        content_endpoint = client.metadata.contents


API methods
===========

Read
----

Retrieves one resource given its reference and owner and returns the response retrieved.

    .. code-block:: python

        endpoint.read(owner, ref)


Browse
------

Retrieves the list of resources that matches with the criteria and returns the response.

    .. code-block:: python

        endpoint.browse(owner, criteria)

Store
-----

Creates one or more resources and returns the response retrieved.

    .. code-block:: python

        endpoint.store(owner, json)


Criteria API for Requesting Data
================================

The SDK supports a fluent criteria API to abstract client code from
the details of the Sequoia query syntax.
This API allows to provide filters to retrieve the queried data and a way to request for related resources and its fields:

Criterion
---------

The way to provide the filter to get specific data is by using the criterion this way.

    .. code-block:: python

        endpoint.browse("testmock",
            Criteria().add_criterion(StringExpressionFactory.field("contentRef").equal_to("testmock:sampleContent"))
        )

This alternative way is also supported:

    .. code-block:: python

        endpoint.browse("testmock",
            Criteria().add(criterion=StringExpressionFactory.field("contentRef").equal_to("testmock:sampleContent"))
        )

The following filtering criteria are supported:

equalTo
~~~~~~~
    .. code-block:: python

        StringExpressionFactory.field("engine").equal_to("diesel")

Will generate the criteria expression equivalent to: field=diesel (withEngine=diesel)

Inclusion of related documents
------------------------------

The SDK support inclusion of related documents up to 1 level (direct relationships).

Both, direct and indirect relationships, are allowed. In each case resource's *reference* are needed to perform the mapping.

    .. code-block:: python

        Criteria().add_inclusion(Inclusion.resource('assets'))

This alternative way is also supported:

    .. code-block:: python

        Criteria().add(inclusion=Inclusion.resource('assets'))

Selecting fields
~~~~~~~~~~~~~~~~

The SDK allows to specify which fields will be present in the response, discarding the rest of them.

For now it can be used only for Inclusions

    .. code-block:: python

        Criteria().add(inclusion=Inclusion.resource('assets').fields('name','ref'))



Paginating results
==================

Iterator
--------

Browse responses can be paginated. To paginate results, browse response has to be used as an iterator.

    .. code-block:: python

        for response in endpoint.browse('testmock'):
            resources = response.resources

Not iterator
------------

If browse function is not used as an iterator, only first page is retrieved. i.e:

    .. code-block:: python

        response = endpoint.browse('testmock')
        resources_in_page_1 = response.resources


With continue
-------------

Sequoia services allow to paginate using the parameter `continue`, which will return the link to get the following page in the `meta` of the response.
The `browse` can be call repeatedly while there are pages to be read.
Optionally, you can set the number of items per page.

    .. code-block:: python

        for response in endpoint.browse('testmock', query_string='continue=true&perPage=2'):
            resources = response.resources


Paginating linked resources
===========================

Inclusion
---------

When doing an inclusion, service returns a list of linked resources. Those resources can be paginated. Let's assume a browse of contents is performed with assets resource as an inclusion. To perform pagination:

    .. code-block:: python

        for linked_assets in endpoint.browse('testmock').linked('assets'):
            for linked_asset in linked_assets:
                asset_name = linked_asset['name']

If linked response is not used as an iterator, only first page of linked resources is retrieved:

    .. code-block:: python

        linked_assets =  endpoint.browse('testmock').linked('assets')
        for linked_asset in linked_assets.resources:
            asset_name = linked_asset['name']



Retrying requests
=================
When a request is returning a retrievable status code, a retry strategy can be configured with ``backoff_strategy``. By default ``backoff_strategy`` is

  .. code-block:: python

   {'wait_gen': backoff.constant, 'interval': 0, 'max_tries': 10}

We can set a different backoff strategy.

    .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        grant_client_id="clientId",
                        grant_client_secret="clientSecret",
                        backoff_strategy={'wait_gen': backoff.expo, 'base':2, 'factor': 1, 'max_tries': 5, 'max_time': 300}
                        )

Here an exponential strategy will be used, with a base of 2 and factor 1.

For more info about backoff strategies https://github.com/litl/backoff

Correlation ID
==============
Every request to Sequoia RESTful services is added with a unique correlation id in the headers.

 .. code-block:: python

        -- request headers --
            ...
            x-correlation-id: f0fca55f3da85..6336cb20fda36
            ...

The SDK allows to set a correlation id at the client to be added to all the subsequent requests.

 .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        ...
                        correlation_id="custom_correlation_id_1234",
                        ...
                        )

        endpoint.browse(owner, criteria)

         -- request headers --
            ...
            x-correlation-id: custom_correlation_id_1234
            ...

It also allows to provide both an user and an application ids so each operation request will be set with
an unique generated correlation id having these values as prefix.
This correlation id will be shared by all related requests derived by that operation: browse, store, etc
(e.g. the subsequents paging requests in a browse operation).

Both parameters `user_id` and `application_id` has to be provided, providing just one
you won't have a prefix in the correlation id.

 .. code-block:: python

        client = Client("https://registry-sandbox.sequoia.piksel.com/services/testmock",
                        ...
                        user_id="user123",
                        application_id="app101",
                        ...
                        )

        endpoint.browse(owner, criteria)

         -- request headers --
            ...
            x-correlation-id: user123/app101/cbd05bd7-3099-4dcb-aeff-806ccec3292a
            ...

        endpoint.browse(owner, criteria)

         -- request headers --
            ...
            x-correlation-id: user123/app101/9becd6c7-8ef0-44c4-a240-6c02c583957f
            ...

The parameter `correlation_id` has precedence over `user_id` and `application_id`.


***********
Development
***********

It has been tested for Python 3.5 and 3.6

You can use the included command line tool `make <make>`_ to work with this project

Preparing environment
=====================

Create new virtualenv
---------------------

It's encouraging to create a new virtual environment and install all the dependencies in it.
You can use these commands:

.. code-block:: python

    mkdir -p ~/.virtualenvs
    virtualenv -p python3.6 ~/.virtualenvs/sequoia-python-client-sdk
    workon sequoia-python-client-sdk
    pip install -r requirements.txt
    pip install -r requirements_test.txt



Testing
=======

There are two different ways of running the tests.

Run tests on the current environment
------------------------------------

Using ``pytest`` option will run all the unit tests over your environment.

.. code-block:: python

    make test

Run tests on every compatible python version
--------------------------------------------

While using the option ``test`` will set up a virtual environment for the supported version of Python, i.e. 3.5 and 3.6 and will run all the tests on each of them.

.. code-block:: python

    make test-all


If you are using `pyenv` and found issues running this command because tox isn't able to create the virtualenvs, just add the python versions you have installed to the file `.python-version` like this:

.. code-block:: bash

    echo "3.6.9" >> .python-version
    echo "3.7.7" >> .python-version
    echo "3.8.3" >> .python-version

Lint
----

To make sure the code fulfills the format run

.. code-block:: python

    make lint

