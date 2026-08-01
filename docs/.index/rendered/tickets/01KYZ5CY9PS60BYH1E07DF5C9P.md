# Compaction watermark can silently drop branch-local events the snapshot never folded

`01KYZ5CY9PS60BYH1E07DF5C9P` · task/bug · **open**

The fold drops any event whose id sorts at or below a compaction watermark, on the assumption that the compaction already folded it into a snapshot.
