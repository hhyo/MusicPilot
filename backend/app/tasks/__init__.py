"""Current background task boundary for MusicPilot.

- Standalone backend mode keeps an in-process polling loop for subscription scheduling.
- MoviePilot plugin runtime registers scheduler services through the host plugin entry.
- Subscription execution runs inline within the application process.
- Pending handoff reconciliation is an inline scheduler follow-up.
- There is currently no separate worker, external queue, or distributed scheduler.
"""
