"""Generate terminal.svg and banner.svg (binary spider + glitch). Usage: python gen.py OUTDIR"""
import random, sys, os

OUT = sys.argv[1]
W, H = 58, 27          # char grid
CX = W // 2
ASPECT = 1.85          # cols per row for round shapes

def blank():
    return [[False] * W for _ in range(H)]

def ellipse(g, cx, cy, ry):
    rx = ry * ASPECT
    for y in range(H):
        for x in range(W):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                g[y][x] = True

def line(g, a, b):
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
    for i in range(n + 1):
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = True

# right-side legs: (attach, knee, tip); left side mirrored
LEGS = [
    ((CX + 5, 9.0),  (CX + 15, 4),  (CX + 21, 0)),
    ((CX + 6, 10.5), (CX + 18, 7),  (CX + 26, 8)),
    ((CX + 6, 12.0), (CX + 18, 15), (CX + 26, 18)),
    ((CX + 5, 13.5), (CX + 15, 19), (CX + 21, 25)),
]

def frame(phase):
    g = blank()
    ellipse(g, CX, 6.5, 2.2)     # head
    ellipse(g, CX, 11, 3.4)      # cephalothorax
    ellipse(g, CX, 18.5, 5.2)    # abdomen
    line(g, (CX - 2, 4), (CX - 3, 2)); line(g, (CX + 2, 4), (CX + 3, 2))  # fangs
    for i, (a, k, t) in enumerate(LEGS):
        for side in (1, -1):
            # tetrapod gait: alternate legs swing forward/back each frame
            s = (1 if (i + (side > 0)) % 2 == 0 else -1) * (1 if phase else -1) * 1.4
            mx = lambda p: (CX + (p[0] - CX) * side, p[1])
            ka, kk, kt = mx(a), mx(k), mx(t)
            kk = (kk[0], kk[1] - s * 0.6)
            kt = (kt[0], kt[1] - s)
            line(g, ka, kk); line(g, kk, kt)
    return g

rng = random.Random(7)
DIGITS = [[rng.choice("01") for _ in range(W)] for _ in range(H)]
EYES = {(CX - 2, 6), (CX + 2, 6), (CX - 1, 6), (CX + 1, 6)}

def rows(g, x0, y0, fs, lh):
    out = []
    for y in range(H):
        s = ""
        for x in range(W):
            if not g[y][x]:
                s += " "
            elif (x, y) in EYES:
                s += '<tspan class="eye">' + DIGITS[y][x] + "</tspan>"
            else:
                s += DIGITS[y][x]
        out.append(f'<tspan x="{x0}" y="{y0 + y * lh}">{s.rstrip()}</tspan>')
    return f'<text font-size="{fs}" xml:space="preserve">' + "".join(out) + "</text>"

FS, LH = 11, 12
SX, SY = 78, 122   # spider top-left in terminal

GLITCH_CSS = """
    .ga { fill: #ffffff; mix-blend-mode: screen; opacity: 0; animation: ga 5s steps(1) infinite; }
    .gb { fill: #b8860b; mix-blend-mode: screen; opacity: 0; animation: gb 5s steps(1) infinite; }
    @keyframes ga { 0%,100% { opacity: 0; transform: none; }
      70% { opacity: .85; transform: translate(-5px,1px); } 71.5% { opacity: .85; transform: translate(4px,-1px); }
      73% { opacity: 0; transform: none; } 88% { opacity: .85; transform: translate(6px,0); } 89% { opacity: 0; transform: none; } }
    @keyframes gb { 0%,100% { opacity: 0; transform: none; }
      70% { opacity: .85; transform: translate(5px,-1px); } 71.5% { opacity: .85; transform: translate(-3px,1px); }
      73% { opacity: 0; transform: none; } 88% { opacity: .85; transform: translate(-6px,0); } 89% { opacity: 0; transform: none; } }
    .s1 { opacity: 0; animation: s1 5s steps(1) infinite; }
    .s2 { opacity: 0; animation: s2 5s steps(1) infinite; }
    @keyframes s1 { 0%,100% { opacity: 0; transform: none; } 70.5% { opacity: 1; transform: translateX(14px); } 72% { opacity: 1; transform: translateX(-9px); } 73% { opacity: 0; transform: none; } }
    @keyframes s2 { 0%,100% { opacity: 0; transform: none; } 71% { opacity: 1; transform: translateX(-16px); } 72.5% { opacity: 0; transform: none; } 88.5% { opacity: 1; transform: translateX(10px); } 89% { opacity: 0; transform: none; } }
"""

def glitch_stack(ref, main_fill, cut1, cut2):
    """main copy + rgb split + two sliced bands of <use href=ref>"""
    return f"""
      <use href="#{ref}" class="ga"/>
      <use href="#{ref}" class="gb"/>
      <use href="#{ref}" fill="{main_fill}"/>
      <use href="#{ref}" fill="{main_fill}" class="s1" clip-path="url(#{cut1})"/>
      <use href="#{ref}" fill="{main_fill}" class="s2" clip-path="url(#{cut2})"/>"""

terminal = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 470" width="1000" height="470">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#14120e"/><stop offset=".6" stop-color="#0a0908"/><stop offset="1" stop-color="#1a150b"/>
    </linearGradient>
    <linearGradient id="silk" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e8b949"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff3c4"/><stop offset="1" stop-color="#c9952a"/>
    </linearGradient>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".35"/></pattern>
    <clipPath id="win"><rect width="1000" height="470" rx="14"/></clipPath>
    <clipPath id="sc1"><rect x="0" y="{SY + 40}" width="1000" height="26"/></clipPath>
    <clipPath id="sc2"><rect x="0" y="{SY + 190}" width="1000" height="18"/></clipPath>
    <clipPath id="hc1"><rect x="0" y="86" width="1000" height="8"/></clipPath>
    <clipPath id="hc2"><rect x="0" y="94" width="1000" height="8"/></clipPath>
    <g id="spA" class="fa">{rows(frame(0), SX, SY, FS, LH)}</g>
    <g id="spB" class="fb">{rows(frame(1), SX, SY, FS, LH)}</g>
    <g id="spider"><use href="#spA"/><use href="#spB"/></g>
    <text id="hey" x="520" y="100" font-size="16">Hey, quexenbp ✦</text>
  </defs>

  <style>
    text {{ font-family: 'Cascadia Code', Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', monospace; }}
    .eye {{ fill: #ffcf4a; }}
    .fa {{ animation: fa .36s steps(1) infinite; }}
    .fb {{ animation: fb .36s steps(1) infinite; }}
    @keyframes fa {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
    @keyframes fb {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
    .crawl {{ transform-box: fill-box; transform-origin: center; animation: crawl 16s ease-in-out infinite; }}
    @keyframes crawl {{
      0%   {{ transform: translate(0,0) rotate(0deg); }}
      18%  {{ transform: translate(-40px,-4px) rotate(-18deg); }}
      30%  {{ transform: translate(-40px,-4px) rotate(-18deg); }}
      50%  {{ transform: translate(45px,4px) rotate(22deg); }}
      64%  {{ transform: translate(50px,16px) rotate(160deg); }}
      80%  {{ transform: translate(-10px,18px) rotate(200deg); }}
      100% {{ transform: translate(0,0) rotate(360deg); }}
    }}
    .cursor {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
{GLITCH_CSS}
  </style>

  <g clip-path="url(#win)">
    <rect width="1000" height="470" fill="url(#bg)"/>

    <rect width="1000" height="38" fill="#050505" opacity=".85"/>
    <circle cx="22" cy="19" r="6" fill="#ff5f57"/><circle cx="42" cy="19" r="6" fill="#febc2e"/><circle cx="62" cy="19" r="6" fill="#28c840"/>
    <text x="500" y="24" text-anchor="middle" font-size="13" fill="#8a857a">quexenbp@github: ~</text>
    <text x="28" y="70" font-size="14" fill="#f2efe8"><tspan fill="#e8b949">❯</tspan> ./spider --wander</text>

    <g class="crawl">{glitch_stack("spider", "url(#silk)", "sc1", "sc2")}
    </g>

    <g font-weight="600">{glitch_stack("hey", "#ffffff", "hc1", "hc2")}
    </g>

    <g fill="none" stroke="#e8b949" stroke-opacity=".55" stroke-width="1.2">
      <path d="M690 124 H520 V276 H960 V124 H790"/>
      <path d="M690 296 H520 V358 H960 V296 H790"/>
    </g>
    <text x="740" y="129" text-anchor="middle" font-size="13" fill="#e8b949">profile</text>
    <text x="740" y="301" text-anchor="middle" font-size="13" fill="#e8b949">status</text>

    <g font-size="14">
      <text x="540" y="152"><tspan fill="#e8b949">├ FOCUS</tspan><tspan x="650" fill="#f2efe8">web · 3D · arduino · security</tspan></text>
      <text x="540" y="174"><tspan fill="#e8b949">├ LANGS</tspan><tspan x="650" fill="#f2efe8">html · c++ · python · js</tspan></text>
      <text x="540" y="196"><tspan fill="#e8b949">│</tspan><tspan x="650" fill="#f2efe8">rust · java · c# · php</tspan></text>
      <text x="540" y="218"><tspan fill="#e8b949">├ TOOLS</tspan><tspan x="650" fill="#f2efe8">blender · figma · vscode · git</tspan></text>
      <text x="540" y="240"><tspan fill="#e8b949">│</tspan><tspan x="650" fill="#f2efe8">burp suite · nmap · wireshark</tspan></text>
      <text x="540" y="262"><tspan fill="#e8b949">└ ROLE</tspan><tspan x="650" fill="#f2efe8">3D artist · developer · security</tspan></text>
      <text x="540" y="324"><tspan fill="#e8b949">├ CREATIVITY</tspan></text>
      <text x="540" y="346"><tspan fill="#e8b949">└ CAFFEINE</tspan></text>
      <text x="916" y="324" fill="#f2efe8">92%</text>
      <text x="916" y="346" fill="#f2efe8">99%</text>
    </g>
    <rect x="650" y="314" width="250" height="10" rx="2" fill="#fff" opacity=".08"/>
    <rect x="650" y="314" width="230" height="10" rx="2" fill="url(#bar)"/>
    <rect x="650" y="336" width="250" height="10" rx="2" fill="#fff" opacity=".08"/>
    <rect x="650" y="336" width="247" height="10" rx="2" fill="url(#bar)"/>

    <g>
      <circle cx="680" cy="388" r="5" fill="#ffffff"/><circle cx="700" cy="388" r="5" fill="#d9d4c7"/>
      <circle cx="720" cy="388" r="5" fill="#8a857a"/><circle cx="740" cy="388" r="5" fill="#2a2620" stroke="#8a857a" stroke-opacity=".5"/>
      <circle cx="760" cy="388" r="5" fill="#fff3c4"/><circle cx="780" cy="388" r="5" fill="#e8b949"/>
      <circle cx="800" cy="388" r="5" fill="#b8860b"/>
    </g>

    <text x="28" y="440" font-size="14" fill="#e8b949">❯</text>
    <rect class="cursor" x="46" y="428" width="9" height="16" fill="#f2efe8"/>

    <rect width="1000" height="470" fill="url(#scan)"/>
    <rect x=".6" y=".6" width="998.8" height="468.8" rx="14" fill="none" stroke="#e8b949" stroke-opacity=".25"/>
  </g>
</svg>
"""

# --- header: heart-shaped spider in 0/1 ---
HEART = """
            +

                                +  ######++                  ++#####++ +
        +                    ########+#+++++                +++++##########+
        +++             #+########+++     ++++             +++     +++###+####+#              +++
      +#++              #####+     #+       +              ++      +#     +#####              ++++
      +###+             #####      +#+       ++++      ++++       +##      #####              ##++
       ####              ####       ##         +++     +++        ##       ####+             ####+
       ++###             +####      +#+        +++    +++        +##      #####       ++    ####+
        ++###+    +++    +#####      ##         +#+   ##         +#      #####+    ++++    ####+
         +####+   +++###    #####    ##+         ##  +#         ++#    +#####   +##+++   +####+
     +     #####      +####  ######   #           #  ##          #+  +#####  +####       ####+
            #####         ##+  #####+ #+          #  #           #  ######  ##+        +####
             #####          +#  ######+           +  +            ######  ##          +####
              +####+          ++  #######       ########    +   ######  ++           #####
  + +           #######         ++ +#######+++#############++########  +         +######           + +
  ++++           ###########        +##############################+  +     ###########           ++++
   #+++             #############     +###########################     #############             +++++
   +#+#+                #############+  ########################   #############                 ++##
    ####+                   ################################################                    ####
     #####+        +++++#+      +#######################################      +##++++        +#####
      ########++++++++++########    ################################    +######++++++++++++#######+
        #########+++               ++++##########################++++               ++++########
         + ########+                     ######################                      ########++
         +++++############################################################################+++++
         ++#++  +#######################################################################   ++##
        +##++      #####+       ++  + ############################+++ ++       +#####      ++##+
         ++###      +                      ##################+                     ++     ###++
           ####+    +                      ##################                      +     ####+
            +###+   +                     ####################                     +   ####+
              ####+ +                    #####+################++                  +  ####+
               +####++                  #####  ##########+ #####+                 ++#####
                 +####                 +####   ### ++ +###  #####                 +####+
                   ####+               #####   +##    ###   +####               +####+
                    +####+             ####+                 ####+             #####
                      +####+           ####+                 ####           +#####
                        ######         #####                 ####         +#####
                          ######+      #####                 ####      ++#####
                            ######     +####                #####     +#####
                              ######   +####                #####   ######+
                                +###########                #####+######+
                                  ###########              +##########
                                    ##########             #########
                                       #######+           ########
                                         #######         ######
                                           ######      ######
                                              ####+   ####+
                                                +##   ##
""".strip("\n").split("\n")

HFS, HLH, HCW = 9, 9, 5.4      # font size, line height, approx char width
HX, HY = 40, 34
hrng = random.Random(11)
NF, TICK_H = 6, .22            # digit frames, seconds per frame
frames_d = [[[hrng.choice("01") for _ in range(120)] for _ in HEART]]
for _ in range(NF - 1):       # each frame flips ~15% of the previous one's digits
    frames_d.append([[(("1" if d == "0" else "0") if hrng.random() < .15 else d) for d in row] for row in frames_d[-1]])

def heart_layer(digits, keep):
    out = []
    for r, line in enumerate(HEART):
        s = "".join(digits[r][c] if ch == keep else " " for c, ch in enumerate(line)).rstrip()
        if s:
            out.append(f'<tspan x="{HX}" y="{HY + r * HLH}">{s}</tspan>')
    return "".join(out)

def heart_frame(digits):
    return (f'<text xml:space="preserve">{heart_layer(digits, "#")}</text>'
            f'<text xml:space="preserve" opacity=".38">{heart_layer(digits, "+")}</text>')

HW = 640
HH = HY * 2 + len(HEART) * HLH
frame_css = "".join(
    f".h{i} {{ opacity: 0; animation: h{i} {NF * TICK_H:.2f}s steps(1,end) infinite; }}\n"
    f"    @keyframes h{i} {{ 0% {{ opacity: {1 if i == 0 else 0}; }} {i * 100 / NF:.3f}% {{ opacity: 1; }} {(i + 1) * 100 / NF:.3f}% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}\n    "
    for i in range(NF))
frame_svg = "".join(f'<g class="h{i}">{heart_frame(d)}</g>' for i, d in enumerate(frames_d))

banner = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {HW} {HH}" width="{HW}" height="{HH}">
  <defs>
    <linearGradient id="gold" x1="0" y1="{HY}" x2="0" y2="{HY + len(HEART) * HLH}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#f2cf6e"/><stop offset=".5" stop-color="#e0a93a"/><stop offset="1" stop-color="#a8701a"/>
    </linearGradient>
  </defs>
  <style>
    {frame_css}
  </style>
  <g fill="url(#gold)" font-family="'Cascadia Code',Consolas,'SF Mono',Menlo,monospace" font-size="{HFS}" font-weight="700">{frame_svg}</g>
</svg>
"""

for name, svg in (("terminal.svg", terminal), ("banner.svg", banner)):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)

# self-check: frames differ (legs move) and body cells are shared
a, b = frame(0), frame(1)
assert a != b
assert a[18][CX] and b[18][CX]
print("ok")
