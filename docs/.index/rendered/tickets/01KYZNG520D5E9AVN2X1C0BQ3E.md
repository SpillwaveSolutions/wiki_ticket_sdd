# Restore full ULID entropy; record git provenance as its own event field

`01KYZNG520D5E9AVN2X1C0BQ3E` · task/bug · **done**

v0.19.0 stamped the short git hash into locally-minted ULIDs by overwriting five characters of entropy.
