# Paper Dragon

An original folded-paper dragon driven by the owner's combined public and private
GitHub contribution calendar. The artwork uses vermilion, ivory, gold seams, ink
clouds and a fixed warm-paper background. It works as a still image too.

## Enable private activity

1. Create an expiring **classic personal access token** with **read:user** only:
   https://github.com/settings/tokens/new . Do not grant repo or workflow scopes.
2. In this profile repository, open Settings → Secrets and variables → Actions →
   New repository secret. Name it **DRAGON_ACTIVITY_TOKEN** and paste the token
   there. Never put the token in a file, issue, chat, or workflow input.
3. Merge the reviewed Paper Dragon branch, then open Actions → Paper Dragon →
   Run workflow on main. Verify the run succeeds and the image appears.

GitHub documents read:user for private/internal contribution collection:
https://docs.github.com/en/graphql/reference/users#contributionscollection .
The collector checks that scope and that the token belongs to dusk9998-max.
Fine-grained tokens and connector credentials are intentionally not used here:
this implementation requires a verifiable classic OAuth scope header.

GitHub may apply account, organization or enterprise policies to what its
contribution calendar returns. This is calendar activity, not a count of every
commit on every branch. See:
https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/viewing-contributions-on-your-profile

## Visual rules

Lifetime calendar totals unlock growth stages at 50, 150, 500 and 1,500
contributions. Gold seams unlock at 25, 100, 300, 750 and 2,000. Earned stage
and gold levels are retained in dragon/state.json; no exact totals are saved.
Activity in the last seven completed UTC days determines a slow 12, 9 or 6
second floating loop. Quiet weeks never remove earned growth.

Calendar totals are used once. The restricted count is not added on top.
The collector queries complete, non-overlapping yearly date windows through
yesterday UTC and rejects missing days, duplicate dates, mismatched totals,
GraphQL errors, identity mismatch and missing read:user scope.

Only the generated SVG and derived growth levels are published. Raw activity,
private/public breakdowns, repo names, code and credentials are never saved.
The public artwork indirectly reflects private activity, by design.
The renderer has no external resources, scripts or dependencies.

## Workflow and recovery

The workflow runs at 00:20 UTC and manually. The personal token is passed only
to the owned collector in a read-only job. A separate contents-write job
publishes the generated SVG/state. All external actions are pinned to SHAs.
Runs are serialized, stale source revisions are rejected, and failed collection
does not publish partial output or replace the last successful artwork.

The old koi workflow becomes manual-only, and its GIF remains for rollback.
Restore the original README embed and schedule to return to the koi.
GitHub may pause scheduled public-repo workflows after prolonged inactivity;
re-enable from Actions if necessary.

## Local commands

    python3 -m unittest discover -s tests -v
    python3 scripts/paper_dragon.py --login dusk9998-max --output-dir dragon

For generation, provide DRAGON_ACTIVITY_TOKEN via your environment or secret
manager. Do not put its literal value in shell history. Tests use tiny fixtures
to exercise edge cases; the committed artwork comes from actual owner activity.
