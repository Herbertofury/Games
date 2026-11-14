# Return-to-tab refresh acceptance

Publication run43570396128 attempt1 failed the return-refresh browser assertion (one observed sync request; expected two); attempt2 passed unchanged. Retain artifact14104182750 and the failed run rather than treating the retry as a repaired product defect. The production policy correctly requires a visible, online, enabled, non-busy session and a cooldown.

The previous harness dispatched a synthetic focus event after a popup login without explicitly foregrounding the original page. A synthetic event is not proof of visibility. It also waited only for an enabled sync button, which can already be enabled when no refresh has started. These are test precondition/observation defects; the historical log alone does not prove which timing caused that single failure.

The harness now waits for initial sync completion, foregrounds the real page and verifies visibility before advancing its clock. For return refresh it records only non-sensitive visibility/online/consent/idle prerequisites, observes the exact backend POST response and its success, then waits for UI completion. Exact request-count, disabled-consent, repeated-focus cooldown and all other checks remain enforced. No production cooldown, visibility requirement, credentials boundary or assertion is relaxed.

PR acceptance runs three independent complete browser sessions, retaining each JSON report. Any failed session fails the job; this is not a retry-until-green loop. Local Node policy tests cover hidden/offline/disabled/busy/pending suppression independently. Browser transport uses the existing explicit mock Steam provider, not a live sign-in. Subsequent full publication and served identity remain separate acceptance steps.
