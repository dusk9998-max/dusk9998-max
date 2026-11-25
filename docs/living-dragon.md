# Living Paper Dragon

## Private access setup

Keep DRAGON_ACTIVITY_TOKEN for the owner contribution calendar (classic read:user).
Add DRAGON_REPO_TOKENS as an Actions secret containing a JSON array of fine-grained
personal access tokens. Create each token under the same profile account, select
All repositories for its resource owner, and grant only Metadata: read and
Contents: read. Use one token per resource owner, including organizations whose
repositories should contribute. Organization approval may be required.
Never paste tokens into a chat, issue, README, or commit.

The collector enumerates all repositories visible to those credentials, including
owner, collaborator and organization membership access, then every readable branch.
GitHub can hide repositories outside a token's authorization: successful collection
cannot prove access to repositories omitted by GitHub. Configure every relevant
resource owner. Fine-grained token limitations or organization policy can prevent
coverage of repositories accessed only as an outside collaborator.

The collector refuses a public-only result and stops on API errors or incomplete
pagination. It retains the previous artwork rather than publishing partial data.
Private repository names, branch names, commit messages and SHAs are never written
to the public output. Aggregate language names and proportions are visible in art.

## Progression

Growth uses the total from GitHub's default contribution calendar (past year).
GitHub determines what activity qualifies and what the authenticated viewer can see.
Compare against the default profile chart under the same visibility settings and
allow for the dragon's last refresh time.
Hatchling starts at 0, Young at 50, Growing at 150, Mature at 500, Elder at 1500.
Gold seals unlock at 25, 100, 300, 750 and 2000 contributions. Earned stages and
seals carry over even when older contributions roll out of the calendar window.

Top-four languages color red paper regions while preserving ivory and texture.
Each repository's language-byte proportions are weighted by the owner's unique
commits there. This describes repository languages, not languages of individual
changed lines. Shared commits are credited once, preferring originals over forks.

A weekly streak means calendar activity in consecutive Monday–Sunday UTC weeks.
The current week has until Sunday to maintain a streak.
Accent fills over 13 weeks and fades over six quiet weeks after a break.
Longest weekly streak is retained permanently: pigment vividness increases over
52 weeks and glimmer intensity over 208 weeks.

Motion uses the trailing seven days including today: zero contributions gives gentle
breathing; 1–9 gives swimming and body undulation; 10+ adds faster motion and a
gold wake. A newly earned stage or seal triggers a brief entrance flourish.
Reduced-motion preference disables movement, and still.svg is always available.

Collection is scheduled at 20 minutes past every hour (UTC) and also supports workflow_dispatch.
No generated preview statistics are used for profile output.

## Interactive portrait

The README image links to the GitHub Pages portrait at
https://dusk9998-max.github.io/dusk9998-max/. README images cannot run interactive
JavaScript. The profile image has no language legend; color inspection is on the
portrait page, with equivalent keyboard buttons and touch selection.

The hourly collector also publishes dragon/stats.json: aggregate calendar contributions,
seven-day contributions, current/record weekly streaks, stage, gold, language proportions,
next-stage remaining contributions and an update timestamp. No private repository names,
branch identities, messages or SHAs are included. Stage thresholds are shared
with the model. A retained stage can exceed the current calendar total; earned
forms persist, but remaining contributions are measured against the next absolute goal.

Enable Pages with GitHub Actions as the publishing source before the first main
run. The render job builds a static portrait artifact without external services;
only a main run that successfully publishes art can deploy it. The deployment job
has Pages and OIDC permissions, and has no repository activity credentials.
Branch runs upload a preview artifact and never deploy the live site.
The static page includes totals and growth progress even without JavaScript.

## Owner refresh

Refresh dragon opens the authenticated Paper Dragon workflow in a new tab. The
owner selects Run workflow on main. The original page checks the public deployed
stats every ten seconds while visible, then reloads both artwork and stats together
when a newer deployment appears. It stops after twenty minutes, or when Stop
watching is selected. Stopping the watcher does not cancel a GitHub run. Network
failures retain the displayed dragon. Public visitors cannot dispatch the workflow.
No activity credentials are sent to the browser; GitHub handles owner authorization.
