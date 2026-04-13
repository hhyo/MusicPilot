"""Current background task boundary for MusicPilot.

- Subscription scheduling runs as an in-process polling loop.
- Subscription execution runs inline within the application process.
- Pending handoff reconciliation is an inline scheduler follow-up.
- There is currently no separate worker, external queue, or distributed scheduler.
"""
