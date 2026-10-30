# Kaelmoor — region bible (draft)

Region 1 of **Poké Legends: Beyond the Nine**. Names were confirmed by Kyle on 2026-10-30.

## Where Lands of Nine left off

Nine lands around one mountain. The player beat every Champion's hall, gathered all 18 plates, faced Arceus in
the Hall of Origin, and beat Kai, the Origin Champion. Team Tempest, the Tidewardens, Wren (Vellorin's Champion),
Prof. Hawthorn and the eight Champions are all canon.

## Premise

**Three years after Origin.** When the 18 plates came back together, the pack ice north of the nine lands split
open, and for the first time ships can reach **Kaelmoor**: a frozen continent ringed around a shattered meteor
crater, outside anything Arceus shaped. An icebreaker expedition sails north from **Rimefall Town** in Vellorin.
You're its youngest member.

Under the ice cap something enormous is sleeping: **Kyurem**, the empty husk left when an ancient dragon split in
two, long before the nine lands. **Team Thaw** wants to melt the ice to reach it.

**Player:** a new trainer, two appearance options (as in Black 2). The hero of Lands of Nine is a legend people
talk about, and nobody knows where they went (a door for a sequel).

## Map

The region is a ring around the crater, travelled clockwise from the hub. Each leg is colder and harsher than the
last, and each one is opened by the badge or expedition gear from the town before it, so there is always exactly one
way forward. The crater (the Hollow Heart) sits in the middle and opens only at the end.

```
                 (4) HOARFROST ──R4── (5) IRONWAKE
                   /                          \
                 R3                            R5
                 /                              \
         (3) CRAGSPIRE      [ HOLLOW HEART ]     (6) EMBERHALT
                 \            (crater)            /
                 R2                              R6
                   \                            /
         (2) DUNEHOLT                   (7) WRAITHMOOR
                     \                       /
                      R1                   R7
                        \                 /
                   (1) PORT SALTMERE ─R8─ (8) RIMEHOLM ── Victory Glacier ── Aurora Spire
                           |                                                 (League, on the rim)
                     ferry south (region 2)
```

**How each leg opens:**

| Leg | From → to | Opened by |
|-----|-----------|-----------|
| R1 | Saltmere → Duneholt | Open from the start |
| R2 | Duneholt → Cragspire | Snowshoes (story, after badge 2) |
| R3 | Cragspire → Hoarfrost | Ice Pick (story, after badge 3), through Cragspire Mines |
| R4 | Hoarfrost → Ironwake | Night freeze: the inlet only freezes over after dark |
| R5 | Ironwake → Emberhalt | Raft (story, after the Ironwake raid) |
| R6 | Emberhalt → Wraithmoor | Heat Lamp (after badge 6) for the blizzard stretch |
| R7 | Wraithmoor → Rimeholm | Grapple (after badge 7) for the rim cliffs |
| R8 | Rimeholm → Saltmere | One-way ice slide home; closes the loop as a shortcut |
| — | Rimeholm → Aurora Spire | 8 badges, through Victory Glacier |
| — | Rimeholm → Hollow Heart | Story: the descent with Ivo |

| # | Town | Gym | Leader | Notes |
|---|------|-----|--------|-------|
| 1 | Port Saltmere | Water | Nerissa | The big Black 2 style hub city: docks, market, expedition HQ, rail station |
| 2 | Duneholt | Ground | Bram | Permafrost village built into frozen dunes |
| 3 | Cragspire | Rock | Tova | Mining town; Regirock's ruin in the old shafts |
| 4 | Hoarfrost | Ice | Elske | Village on a glacier tongue; Regice's ruin under the ice |
| 5 | Ironwake | Steel | Kade | Rusting whaling-port factory city; Registeel's ruin; Team Thaw HQ |
| 6 | Emberhalt | Fighting | Rurik | The one warm place: hot springs and geothermal vents |
| 7 | Wraithmoor | Ghost | Isolde | Fog marsh full of ships frozen in old sea ice |
| 8 | Rimeholm | Dragon | Asger | Last town on the crater rim; keepers of the Kyurem legend |
| — | Aurora Spire | League | Elite Four + Champion | Ice tower on the crater's edge |

Routes between each pair (about 10), plus caves: **Saltmere Undercroft** (sewers and old tunnels under the hub),
**Cragspire Mines**, **Ironwake Drill Site**, and **Victory Glacier** before the League.

## Art direction

Black 2's look, made from scratch: no ripped or traced Black 2 assets.

- **Overworld:** low-poly 3D towns and routes on the DS 3D hardware, modelled in Blender. A tilted camera that swings for big moments (bridges, the Saltmere skyline, the crater descent).
- **Characters:** small 2D sprites (32x32) with 4-direction walk cycles.
- **Battles:** Legends of 9's whole-party battles: your whole party against a wild pack or a trainer's team, every Pokémon commanded, then everyone acting in speed order. Black 2 presentation: 3D-style backdrops per area, official front and back sprites with HP bars on the top screen, and a touch command menu on the bottom that steps through each of your Pokémon.
  - Rules carried from Legends of 9's later versions: party of up to 6, and your whole living party fights. Wild packs are 1 to half your living party (max 3). Route trainers field 2–5, gym juniors 3–4, rivals and leaders 6.
  - DS layout: the top screen shows the field. The bottom screen lists every Pokémon's HP and lets you tap targets. Battle sprites are full size (96x96) with up to 3 a side and shrink to 64x64 with 4–6 a side, so a full 6v6 fits.
- **UI:** clean, flat Black 2 style menus and text boxes across both screens.
- **Kaelmoor palette:** pale blues and whites by day, deep navy and aurora greens at night, warm orange only in Emberhalt.

## Signature mechanic: the thaw cycle

The real-time clock drives temperature. **By day**, lakes and inlets thaw: you Surf across them, and water
Pokémon appear. **By night** they freeze: you walk or slide across the ice, ice-sliding puzzles appear, and the
encounter pools change. Some items and paths only exist on one side of the cycle.

**Expedition gear replaces HMs.** It's handed out by the story, and no move slots are wasted:
Ice Pick (break ice blocks), Snowshoes (deep snow), Grapple (cliffs), Raft (open water), Heat Lamp (blizzard routes).

## Story

**Prologue.** Aboard the icebreaker *Northwind*. **Prof. Hawthorn** sends you, and the expedition is led by his
colleague **Prof. Halvard**. **Hale**, Rimefall's gym leader from Legends of 9, sees you off and gives you your
starter. You meet the rival, **Ivo**, Halvard's kid, who resents a newcomer taking "his" place on the expedition.

**Act 1 (badges 1–2): arrival.** You land at Port Saltmere and set up camp. The first heat-drill holes appear in
the ice, along with "LET IT MELT" graffiti. Team Thaw is introduced as eco-radicals who say the ice cap is a prison.

**Act 2 (badges 3–5): the golems.** In the ruins you find the three Regis, sealed as guardians that keep the Hollow
Heart frozen. Team Thaw's leader **Dr. Sefa Varn** and her admins **Brann** and **Mira** are breaking the seals one by one.
The act ends with a raid on their HQ in Ironwake, and you fight Brann. **Kai**, the Origin Champion, turns up after
badge 4, has heard of you, and battles you once at a fixed level as a test.

**Act 3 (badges 6–8): the melt.** Thaw sets off a geothermal drill under Emberhalt. Lakes stop refreezing, and the
thaw cycle breaks across half the map until you stop it. The twist: Halvard has been funding Thaw, because he
believes the melted crater will reveal where Kyurem's lost halves went. Ivo has to choose a side. He picks you.

**Climax: the Hollow Heart.** You descend into the crater with Ivo. Varn wakes Kyurem, and it goes berserk without
its halves. You battle and catch it (or calm it, with a retry, like Lugia in Legends of 9). The ice cap refreezes.

**Ending.** Victory Glacier, then the Aurora Spire League. Ivo is the Champion, as Wren was in Legends of 9.

**Post-game.** **Wren** runs a battle facility at Port Saltmere, and the Challenge Tower from Legends of 9 returns.
Bring the three Regis to the **Titan's Vault** for Regigigas. Halvard's notes point south across the
sea to where the white and black dragons fell. That's the hook for region 2, with Reshiram and Zekrom.

## Game structure

- Normal level scale (cap 100), not Lands of Nine's 900: a clean start for new players.
- Carried over from Lands of Nine: Nuzlocke mode (chosen at New Game) and a post-game tower.

## Cast

| Role | Name | Party theme |
|------|------|-------------|
| Rival | Ivo | Mirrors your starter; ends on Ice/Dragon |
| Professor | Halvard | Expedition lead, secretly backing Thaw |
| Sender | Prof. Hawthorn | Professor from Legends of 9 |
| Mentor cameo | Hale | Ice gym leader from Legends of 9 |
| Returning | Kai | Origin Champion; one test battle after badge 4 |
| Returning | Wren | Vellorin's Champion; post-game battle facility |
| Villain boss | Dr. Sefa Varn | Fire/Steel (heat machines) |
| Admins | Brann, Mira | Fire / Water |

## Pokémon

Official sprites. The wild roster leans cold: tundra, marsh, mines, hot springs and sea ice, from all generations.

**Starters.** In the prologue, Hale offers every base starter from Gen 1 to Gen 9, all 27 of them, on a
grid on the touch screen. Highlighting a starter (moving the D-pad cursor onto it, or tapping it once) shows a short preview on the top screen: its
animated sprite, name, type, a line of flavour text and its final evolution. Tapping again confirms the pick.

| Gen | Grass | Fire | Water |
|-----|-------|------|-------|
| 1 | Bulbasaur | Charmander | Squirtle |
| 2 | Chikorita | Cyndaquil | Totodile |
| 3 | Treecko | Torchic | Mudkip |
| 4 | Turtwig | Chimchar | Piplup |
| 5 | Snivy | Tepig | Oshawott |
| 6 | Chespin | Fennekin | Froakie |
| 7 | Rowlet | Litten | Popplio |
| 8 | Grookey | Scorbunny | Sobble |
| 9 | Sprigatito | Fuecoco | Quaxly |

Ivo then takes the starter of the same generation whose type beats yours, as rivals did in the old games.

## Names

Confirmed 2026-10-30.

| Kind | Names |
|------|-------|
| Region and landmarks | Kaelmoor, Hollow Heart (crater), Aurora Spire (League), Titan's Vault (Regigigas), icebreaker *Northwind* |
| Towns | Port Saltmere, Duneholt, Cragspire, Hoarfrost, Ironwake, Emberhalt, Wraithmoor, Rimeholm |
| Caves | Saltmere Undercroft, Cragspire Mines, Ironwake Drill Site, Victory Glacier |
| Gym leaders | Nerissa (Water), Bram (Ground), Tova (Rock), Elske (Ice), Kade (Steel), Rurik (Fighting), Isolde (Ghost), Asger (Dragon) |
| Story cast | Ivo (rival), Prof. Halvard, Dr. Sefa Varn (Thaw boss), Brann and Mira (admins) |
| Villain team | Team Thaw |
| Expedition gear | Ice Pick, Snowshoes, Grapple, Raft, Heat Lamp |
| Still unnamed | The Elite Four, and the route names |

Returning names from Legends of 9 (Hawthorn, Hale, Kai, Wren, Rimefall Town) stay as they are.

## Title

**Poké Legends: Beyond the Nine** (chosen 2026-10-30).
