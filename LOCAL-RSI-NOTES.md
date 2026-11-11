# Local RSI integration branch

This is an isolated development branch in IamSpicyBar/sift, based on upstream
558d1465e87dd14cce5530b44b93aa2962a679b9. It is not an upstream release and does
not change HMBot Studio's published dependency lock or the completed A/B record.

It preserves generic local fixes for packaged resources, configured transport,
input/output evidence separation, full process and final-answer evidence, bounded
judge inputs and explicit gate candidate identity. The resource and gate subsets
were proposed separately upstream as PRs #15 and #16; neither is merged here.

Validation: 1,862 tests passed, 10 skipped; final focused gate run 48 passed;
git diff --check passed. Independent review found generic fixes rather than a
Pilot-specific adapter. These checks are not a new real-model E2E measurement.

The separate npm dsh-eval-suite process-tree experiment is not included. Review
found a cancellation regression when ps is unavailable, so it remains unpublished.
