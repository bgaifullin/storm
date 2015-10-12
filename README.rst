Storm
=====
.. image:: https://travis-ci.org/bgaifullin/storm.svg
    :target: https://travis-ci.org/bgaifullin/storm

 .. image:: https://coveralls.io/repos/bgaifullin/storm/badge.png?branch=master
    :target: https://coveralls.io/r/bgaifullin/storm?branch=master


The library to easy build rest-full web services based on asynchronous frameworks
Module based ideology

Example
*******

.. code:: python

  import storm

  REQUIRES = ("urlfetch",)

  SETTINGS = [
    {
       "name": "opt1",
       "help": "the option"
    }
  ]

  EXCEPTIONS = {ValueError: 400}


  @storm.handler('get', 'test', wrap='json.output', secure=False)
  def test(context, number: int, values: str, optional: bool=False):
      return [number, values, optional]


Arguments:
**********
* **method** The http method, see `HTTP-Methods`_
* **url** The resource uri, can be relative or absolute
* **secure** If True, the method requires authentication, default: True.
* **status** Specify HTTP status for response, default: 200.
* **mutator** the comma separated list of mutators, that can be applied for arguments and result, to more details see section `MUTATORS`_.


The function arguments are converted to input arguments by using standard python function argument
annotation.

.. code::

  <name>:[<type>] [=default]


META INFORMATION
================

Each module can declare the following global variables:

REQUIRES
********
The list of required modules, list of available modules: `Modules`_

SETTINGS
********
The optional settings, that should be provided by user

EXCEPTIONS
**********
The exceptions class with associated http status, may be function f(e),
where `e` is exception value.

HTTP-Methods
============
* **get** "The HTTP GET method handler.
* **put** "The HTTP PUT method handler.
* **post** "The HTTP POST method handler.
* **delete** "The HTTP DELETE method handler.
* **getx** The method to get one instance, in case if argument \"$key\" is specified.
* **query** The method to get list of elements in case if argument \"$key\" is not specified.


Modules
=======
* **sql** The sql database connector

  * *sql_master* The comma separated list of master nodes
  * *sql_slave*  The coma separated list of slave nodes
  * *sql_user*  The username
  * *sql_password*  The username
  * *sql_timeout*  The connection timeout
  * *sql_retries*  The retries limit
  * *sql_delay*  The timeout between retries

* **urlfetch** The async http client

  * *urlfetch_root_ca* The root CA
  * *urlfetch_validate_cert* The certificate to validate server certificate
  * *urlfetch_client_cert* The client certificate
  * *urlfetch_client_key*  The client key

* **google** The google API client
  * *google_api_key* The google application key
  * *google_secret* The google application secret

Mutators
========
* **json** the json input and output formatting
* **json.ouput** transform only the function result
