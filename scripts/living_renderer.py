"""Self-contained language-colored growth forms with continuous body animation."""
import colorsys
from html import escape
from living_model import STAGE_NAMES
from dragon_art import embedded_art

FORMS = ("hatchling.png", "young.png", "dragon.png", "mature.png", "elder.png")
NAMES = STAGE_NAMES


def color_filter(identifier, hue, saturation):
    # Red-vs-gold discriminator: R - 2G + B. Ivory and gold are excluded, so
    # language colors tint red paper panels rather than recoloring the whole art.
    return f'''<filter id="{identifier}" color-interpolation-filters="sRGB">
<feColorMatrix in="SourceGraphic" type="hueRotate" values="{hue:.3f}" result="hue"/>
<feColorMatrix in="hue" type="saturate" values="{saturation:.3f}" result="paint"/>
<feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  4 -8 4 0 -.08" result="red"/>
<feComposite in="paint" in2="red" operator="in"/>
</filter>'''


def render_living(model, animated=True):
    state, palette = model["state"], model["palette"]
    stage, mood = state["stage"], model["mood"]
    speed = {"rest": 10, "active": 6, "busy": 4.5}[mood]
    amplitude = {"rest": 2, "active": 10, "busy": 16}[mood]
    definitions, panels = [], []
    start = 0
    for i, item in enumerate(palette):
        color = item["color"].lstrip("#")
        rgb = tuple(int(color[j:j + 2], 16) / 255 for j in (0, 2, 4))
        hue = colorsys.rgb_to_hsv(*rgb)[0] * 360 - 10
        definitions.append(color_filter("language-" + str(i), hue, model["vividness"]))
        height = 640 * item["share"]
        definitions.append(f'<clipPath id="panel-{i}"><rect x="0" y="{start:.3f}" width="800" height="{height + .5:.3f}"/></clipPath>')
        panels.append(f'<use data-language-index="{i}" aria-label="{escape(item["name"], quote=True)}" href="#dragon-art" filter="url(#language-{i})" clip-path="url(#panel-{i})"/>')
        start += height
    definitions.append(color_filter("streak-accent", 38, 1.1))
    definitions.append('<clipPath id="fins"><path d="M0 300H380V420H800V640H0Z"/></clipPath>')
    painted = '<use href="#dragon-art"/>' + "".join(panels)
    painted += f'<use href="#dragon-art" filter="url(#streak-accent)" clip-path="url(#fins)" opacity="{model["accent"]:.4f}"/>'
    wave = f'<animate attributeName="baseFrequency" values="0 .006;0 .012;0 .006" dur="{speed}s" repeatCount="indefinite"/>' if animated else ""
    style = ""
    if animated:
        arrival = "animation: unfold 2s ease-out 1;" if model["milestone"] else ""
        style = f'''<style>
@keyframes swim {{0%,100% {{transform:translate(-10px,8px) rotate(-2deg)}}50% {{transform:translate(10px,-8px) rotate(2deg)}}}}
@keyframes breathe {{0%,100% {{transform:scale(1)}}50% {{transform:scale(1.018)}}}}
@keyframes wake {{0% {{opacity:0;transform:translate(0,0)}}25% {{opacity:.7}}100% {{opacity:0;transform:translate(-60px,30px)}}}}
@keyframes glimmer {{0%,100% {{opacity:0}}50% {{opacity:{model["metallic"] * .18:.3f}}}}}
@keyframes unfold {{from {{transform:scale(.92) rotate(-5deg)}}to {{transform:scale(1) rotate(0)}}}}
@media (prefers-reduced-motion: no-preference) {{
 .body {{filter:url(#body-wave)}}
 .creature {{transform-origin:400px 320px;animation:{"breathe" if mood == "rest" else "swim"} {speed}s ease-in-out infinite}}
 .wake {{animation:wake {speed}s linear infinite}}
 .metallic {{animation:glimmer 7s ease-in-out infinite}}
 .arrival {{transform-origin:400px 320px;{arrival}}}
}}
</style>'''
    background = embedded_art("background.jpg")
    sprite = embedded_art(FORMS[stage])
    gold = "".join(f'<circle cx="{650 + i * 23}" cy="609" r="4" fill="#c49a51"/>' for i in range(state["gold"]))
    wake_marks = ""
    if mood == "busy":
        wake_marks = "".join(f'<circle class="wake" cx="{160 + i * 18}" cy="{500 - i * 6}" r="{2 + i % 2}" fill="#c49a51" opacity="0" style="animation-delay:{-i * .65}s"/>' for i in range(6))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="640" viewBox="0 0 800 640" role="img" aria-labelledby="title desc">
<title id="title">{NAMES[stage]} Paper Dragon</title>
<desc id="desc">A {NAMES[stage].lower()} folded-paper dragon. Language mix colors the paper panels; weekly streaks fill fins with gold, record streaks enrich the pigments. Motion mode: {mood}. Public and authorized private working branches contribute.</desc>
{style}
<defs>
<image id="dragon-art" x="26" y="20" width="748" height="600" preserveAspectRatio="xMidYMid meet" href="{sprite}"/>
<filter id="body-wave" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">
<feTurbulence type="turbulence" baseFrequency="0 .006" numOctaves="1" seed="7" result="water">{wave}</feTurbulence>
<feDisplacementMap in="SourceGraphic" in2="water" scale="{amplitude}" xChannelSelector="R" yChannelSelector="G"/>
</filter>
{''.join(definitions)}
</defs>
<image width="800" height="640" preserveAspectRatio="xMidYMid slice" href="{background}"/>
{wake_marks}
<g class="arrival"><g class="creature">
<g class="body">{painted}</g>
<use class="metallic" href="#dragon-art" opacity="0"/>
</g></g>
{gold}
</svg>'''
