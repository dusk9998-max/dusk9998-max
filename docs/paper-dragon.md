# Paper Dragon

A reference-matched folded-paper dragon driven by the owner's combined public
and private GitHub contribution calendar. The detailed head, flowing S-shaped
body, layered ivory mane, textured vermilion paper and gold flowers are visible
at every stage. The dragon floats independently over a textured paper backdrop,
red sun and ink clouds. A still version is also available.

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
contributions. Additional gold floral seals unlock at 25, 100, 300, 750 and 2,000. Earned stage
and gold levels are retained in dragon/state.json; no exact totals are saved.
Activity in the last seven completed UTC days determines an 8, 6 or 4.5
second floating and rocking loop. Quiet weeks never remove earned growth.
The dragon moves through a 36-unit vertical range and rocks between -3 and +3
degrees. Animation is enabled only when the viewer has no reduced-motion
preference. The README also links to dragon/still.svg for viewing without motion.
Growth scales the same detailed artwork from 84% to 98%; it no longer adds
geometric segments. The reference's original flowers and seams remain visible
at every level; earned seals are separate ornaments along the lower edge.

Calendar totals are used once. The restricted count is not added on top.
The collector queries complete, non-overlapping yearly date windows through
yesterday UTC and rejects missing days, duplicate dates, mismatched totals,
GraphQL errors, identity mismatch and missing read:user scope.
Collection starts on January 1 of the account's creation year: GitHub may
attribute early activity to a calendar day preceding the UTC creation date.

Only the animated/still SVGs and derived growth levels are published. Raw activity,
private/public breakdowns, repo names, code and credentials are never saved.
The public artwork indirectly reflects private activity, by design.
The renderer embeds the local dragon PNG and background JPEG directly into each
SVG, so GitHub's image mode needs no external image requests. Source assets live
in assets/paper-dragon/. Neither image generation nor image conversion runs in
the nightly workflow; the standard-library renderer reuses the committed assets.

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
