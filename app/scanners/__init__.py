"""External monitoring scanners.

Scanners are infrastructure adapters responsible only for communicating
with external monitoring targets and returning structured results.

They must not:

* access PostgreSQL;
* contain FastAPI logic;
* persist measurements;
* calculate application-level camera status.
  """