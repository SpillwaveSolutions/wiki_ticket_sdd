# Fix plan-capture slug-scoped duplicate guard (PR #198)

`01KYGVDKEWT513AGM0ZTY3SZP0` · task/bug · **open**

Rick's downstream harness_engineering_book repo hit a real bug: plan-capture's overwrite guard checked only today's UTC-dated filename, so a plan authored in local evening time (behind UTC) silently duplicated with tomorrow's date.
