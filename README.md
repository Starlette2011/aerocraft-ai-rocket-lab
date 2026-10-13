# AeroCraft AI - Rocket Lab

Draw a rocket (or photograph one), see it in 3D, then launch it.

AeroCraft is a single-page rocket design and flight simulator built for BananaHacks. You sketch the side outline of a rocket on a canvas, or upload a photo of a hand-drawn one, and the app builds a 3D model from that exact outline. Then you fly it through a physics simulation with real atmosphere and gravity. An auto-tuner can pick the engine and parachute settings for you.

It's one HTML file with no build step and no server.

## Running it

Open `index.html` in a browser. That's it.

The page loads Tailwind, Three.js (r128) and one Google Font from CDNs, so you need an internet connection the first time. To host it, drop the file in a GitHub repo and turn on GitHub Pages (Settings, then Pages, then deploy from the main branch). Because the file is named `index.html`, the repo URL works as the app link.

Want to see everything in 60 seconds? Click **Autopilot Demo** in the header.

## How to use it

1. **Draw or upload.** In the Studio tab, draw the outline of a rocket on the sketchpad, click a preset (Pencil Launcher, Heavy Lifter, Delta Wing, Sci-Fi Cruiser), or click **Upload Photo** to use a picture of a drawing on paper. The 3D model updates after every stroke.
2. **Adjust.** Use the tabs on the left (Nose, Fuselage, Fins, Engine, Mission) to change shapes, colors, fuel, thrust, propellant, payload and parachute settings. Changing the nose, body or fin-span controls by hand drops the sketch and goes back to the built-in shapes. Colors, engines, payload, parachute and the target keep it.
3. **Paint it.** **Paint Hull** wraps any picture onto the rocket's body as a texture. **Clear Paint** removes it.
4. **Set a target.** On the Mission tab, pick a target apogee (3 km, 30 km or 100 km). The design review underneath shows a predicted apogee and landing speed as you edit.
5. **Auto-tune (optional).** Click Auto-Tune Engine & Chute and the app searches for thrust, propellant, parachute size and deploy altitude that hit your target and land safely.
6. **Launch.** Go to the Launch Simulator tab, pick a speed (1x to 50x) and hit Launch. With sound on, a spoken T-minus countdown plays first. You get live telemetry, a flight graph and a sky that changes with altitude.
7. **Record, save or share.** **Record Flight** saves the launch view as a video, **Save PNG** saves a still, and **Share Link** copies a link that reopens your exact rocket.
8. **Read the report.** After touchdown you get apogee, top speed, max Q, landing speed and a score out of 100.

## Features

### Photo to rocket

Upload a photo of a hand-drawn rocket and the page turns it into a clean silhouette, then feeds it through the same pipeline as a hand-drawn sketch. It runs entirely in the browser.

1. The photo is shrunk to about 260 px on its longest side and converted to grayscale. Light drawings on dark paper are flipped automatically.
2. **Ink** is any pixel clearly darker than the average of its neighborhood, so shadows and uneven lighting don't matter.
3. Small gaps in the pen line are closed. Anything the outside can't reach (a flood fill from the image border) is the inside of the rocket.
4. The biggest blob is kept. If it's lying on its side it is turned upright, and it is flipped if needed so the narrow end (the nose) is on top.
5. The silhouette is measured row by row, lightly smoothed and drawn onto the sketchpad. From there the normal sketch reader takes over.

Tips: dark pen on plain paper, good light, the whole rocket in frame, and a closed outline. If nothing usable is found you get a message under the sketchpad instead of a broken model.

### Autopilot demo

One click runs a full tour: it draws a rocket stroke by stroke, shows the 3D model build from it, runs Auto-Tune for 100 km, launches on Earth and fast-forwards, then switches to Mars, tunes for 30 km with a landing burn, and flies again. Captions explain each step. Click the button again to stop it. It's the quickest way to see the whole app, and it makes good video footage.

### Record flight

**Record Flight** captures the Launch Simulator view as a `.webm` video and downloads it when you stop (or when you close the flight report). It needs a browser with MediaRecorder, such as Chrome, and the Launch Simulator tab open.

### Paint your rocket

**Paint Hull** takes any image and wraps it onto the rocket body as a texture in the 3D view. **Clear Paint** goes back to the plain body color. **Save PNG** on the 3D view saves the painted rocket as an image.

### Shareable links

**Share Link** packs the whole design into the page URL (after the `#`) and copies it. That covers the planet, every slider and menu, the target, and the sketch outline (sampled at 48 heights). Open the link and the same rocket appears. Nothing is uploaded anywhere, and a link made on one machine works on any other. Painted hull images are not included in links.

### Sound and countdown

Sound uses the Web Audio API and the browser's built-in speech. With sound on, Launch runs a spoken 3, 2, 1, Liftoff countdown with beeps. During flight the engine rumble follows the thrust, fades as the air thins, and is quieter at high fast-forward speeds. Parachute opening, landing and crashing each have their own sound. The **Sound** button turns it all off.

## How the sketch becomes a rocket

The sketch reader scans the canvas row by row and records how wide the outline is at each height. From that it works out:

- the body width, using the median width through the middle of the drawing
- where the nose ends, which is the first row that reaches about 90% of the body width
- how curved the nose is, which picks conical, parabolic or ogive for the drag value
- the fins, which are any parts of the outline that stick out past the body

All of it uses one pixel-to-metre scale, so the proportions match what you drew. The body is the outline revolved around the vertical axis. Each fin is the exact flared shape from your drawing, extruded flat and copied around the rocket using the fin count. In the side view it lines up with the sketch. Photos go through the same reader once they've been turned into a silhouette.

For the best result, draw a closed, left-right symmetric outline. Use the Spin button to switch between a still side view and a slowly rotating one.

## backend.py (OpenCV prototype)

`backend.py` is a small Python script that does the same sketch and photo analysis with OpenCV. It isn't connected to the web app. `index.html` runs entirely in the browser and never calls it, so the 3D model and the simulation don't depend on it.

**Sketch mode** (default):

1. Blurs the image and runs Canny edge detection.
2. Takes the largest outside contour and fills it in to get a solid silhouette. This works for both filled shapes and thin outlines.
3. Measures the width of the silhouette at every row, then splits it up the same way the browser version does: body width from the middle of the drawing, nose end where the width reaches about 90% of the body, nose shape from how curved the nose is, and fins from rows wider than the body.
4. Converts the pixel measurements to the app's slider values (nose height, body length, body diameter, fin span, nose shape) using one scale for both axes, plus a rough drag coefficient from the same formula the app uses.

**Photo mode** (`--photo`) follows the same steps as the browser's photo-to-rocket: an adaptive threshold finds the ink, a dilate closes pen gaps, the outside is found by labeling connected regions that touch the border, the biggest blob is cropped and stood upright with the nose on top, and its row widths are smoothed and sent through the same feature splitter. A sideways or upside-down photo gives the same result as an upright one.

If it finds nothing, it returns `{"status": "No valid geometry detected"}`.

To try it:

```
pip install opencv-python numpy
python backend.py                    # runs a built-in pencil-rocket test sketch
python backend.py sketch.png         # analyzes a drawn sketch
python backend.py photo.jpg --photo  # analyzes a photo of a drawing on paper
```

For sketch mode, dark lines on a light background are flipped automatically, and PNGs with transparency are treated as a mask. It prints the measurements in pixels and the converted rocket parameters. The outline thickness isn't compensated for the way the browser version does, so results can be a pixel or two wider.

## Planets

The Destination menu in the header switches the world. It changes the physics, the 3D scene, the launch view and the color of the whole interface.

| World | Gravity (m/s2) | Surface air (kg/m3) | Scale height (m) | Speed of sound (m/s) |
|-------|---------------|---------------------|------------------|----------------------|
| Earth | 9.81 | 1.225 | 8,500 | 340 |
| The Moon | 1.62 | none | none | none |
| Mars | 3.71 | 0.020 | 11,100 | 240 |
| Venus | 8.87 | 65 | 15,900 | 410 |
| Titan | 1.35 | 5.3 | 20,000 | 195 |

Gravity, air density, drag, thrust-to-weight, Max Q and Mach number all use the selected world's values, and so do the design review and Auto-Tune. Some consequences:

- On the Moon there's no air, so a parachute does nothing. Use the **Landing Fuel Reserve** slider to keep propellant for a landing burn.
- Mars has air too thin for a parachute to land a heavy rocket, so it also needs a landing burn.
- Venus air is so thick that drag matters a lot and parachutes work extremely well.
- Titan has low gravity and thick air, so flights are long and gentle.

The landing burn lights the engine at full thrust when the stopping distance catches up with the altitude. You can't change worlds in the middle of a flight.

## The physics

Flight is a vertical, one-dimensional simulation using Euler integration at a fixed 20 ms step.

- **Gravity** is the world's surface gravity, falling off with altitude (inverse square).
- **Air density** is exponential, using the world's surface density and scale height, and zero above ten scale heights (85 km on Earth).
- **Thrust and burn rate** come from engine thrust times the number of engines, and fuel Isp (RP-1 310 s, methane 380 s, hydrogen 450 s). Mass drops as propellant burns.
- **Drag** is `0.5 * rho * v^2 * Cd * A`. Cd comes from the nose shape plus a small fin term, and the parachute adds drag once it opens.
- **Parachute** opens when the rocket is falling and drops below the deploy altitude.
- **Landing burn** (optional): with a fuel reserve set, the engine re-lights on the way down to slow the rocket.
- **Landing** at 8 m/s or faster counts as a crash.

Fast-forward doesn't change the result. The sim always takes the same fixed steps, and the speed setting only decides how many it runs per frame. A 50x flight gives the same numbers as a 1x flight.

## Auto-tune and design review

Both use a headless copy of the same flight physics, with nothing drawn on screen.

Auto-tune is a random hill-climb: 360 tries, each nudging thrust, propellant, landing reserve, parachute size and deploy altitude (big jumps early, small ones later). The first 300 tries use coarser time steps for speed, and the last 60 use the exact physics, keeping whichever is closest to the target apogee while landing under 7 m/s and lifting off with a thrust-to-weight ratio of at least 1.15. It's a search algorithm, not a machine-learning model, and because it's random, two runs can give slightly different answers. A run takes a second or two on Earth and up to ten seconds on some worlds, and the button shows "Tuning..." while it works. The Moon is the hardest to land on, so if a run misses, click it again. Predictions match a real launch exactly, since both use the same physics.

The design review checks static stability (in calibers), thrust-to-weight, and the predicted apogee and landing speed.

## Score

`100 * (1 - |apogee - target| / target)`, never below 0, and halved if the rocket crashes.

## Known limits

- Flight is straight up and down. There's no wind, steering or sideways motion, so stability is reported but doesn't change the trajectory.
- The body is round, so a sketch matches from the side but not from the front.
- With an odd fin count (like 3), the fins aren't mirrored in the side view. Use 4 or 6 to match the sketch exactly.
- Stages and stage rings are visual only. Staging isn't simulated.
- Mach number uses each world's speed of sound, and there's no transonic drag or heating model.
- Photo-to-rocket needs a reasonably clear, closed outline. Faint pencil, heavy glare, a busy background, or an outline with big gaps can fail or give an odd silhouette. Several separate objects in the photo are reduced to the biggest one.
- Photo-to-rocket reads the outer edges of each row, so inner details and concave notches are ignored. Several strokes on the sketchpad get merged into one outline.
- Share links hold the design, planet and target, but not a painted hull image. A link also drops the sketch to 48 sampled heights, so fine details can soften.
- Record Flight needs MediaRecorder (Chrome, Edge and recent Firefox work) and saves `.webm`. Speech for the countdown depends on the voices your browser has.
- `backend.py` isn't wired into the web app. Connecting them would need a small server (Flask or FastAPI, for example) that the page sends the image to.
- Mass, center of mass and center of pressure are simple estimates, good for comparing designs rather than for real engineering.

## Built with

Plain HTML, CSS and JavaScript for the app, [Tailwind CSS](https://tailwindcss.com) (CDN), [Three.js](https://threejs.org) r128 for the 3D view, the Canvas API for the sketchpad, photo processing, graph and flight view, MediaRecorder for flight video, and the Web Audio and Speech Synthesis APIs for sound. The `backend.py` prototype uses Python, OpenCV and NumPy.

## Files

- `index.html`: the whole app
- `backend.py`: standalone OpenCV version of the sketch and photo analysis (not used by the app)
- `README.md`: this file
