# Plugin hooks never fired: the manifest was not wrapped

`01KZC47J0FF1EBGD1JH3GP28RQ` · task/bug · **done**

The plugin's hook manifest declares its events at the top level, but the loader reads them from under a top-level hooks record.

## Release

- [[Release-v0.22.1]]
