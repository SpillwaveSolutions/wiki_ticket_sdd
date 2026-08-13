# Fix TestStrictIsPassable dependency on ambient git clone depth

`01KZY0B9KQBKH6NFGBA0YFSYQA` · task/bug · **done**

The two new tests in TestStrictIsPassable call doc_verify.verify() in whatever directory the test runner stands in.
