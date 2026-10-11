# AeroCraft AI - Rocket Lab

Draw a rocket, see it in 3D, then launch it.

AeroCraft is a single-page rocket design and flight simulator built for BananaHacks. You sketch the side outline of a rocket on a canvas, the app builds a 3D model from that exact outline, and then you fly it through a physics simulation with real atmosphere and gravity. An auto-tuner can pick the engine and parachute settings for you.

It's one HTML file with no build step.

## Running it

Open `aerocraft.html` in a browser. That's it.

The page loads Tailwind, Three.js (r128) and one Google Font from CDNs, so you need an internet connection the first time. To host it, drop the file in a GitHub repo and turn on GitHub Pages (Settings, then Pages, then deploy from the main branch). Rename it to `index.html` if you want the short URL.

## How to use it

1. **Draw.** In the Studio tab, draw the outline of a rocket on the sketchpad, or click a preset (Pencil Launcher, Heavy Lifter, Delta Wing, Sci-Fi Cruiser). The 3D model updates after every stroke.
2. **Adjust.** Use the tabs on the left (Nose, Fuselage, Fins, Engine, Mission) to change shapes, colors, fuel, thrust, propellant, payload and parachute settings. Touching a slider drops the sketch and goes back to the built-in shapes.
3. **Set a target.** On the Mission tab, pick a target apogee (3 km, 30 km or 100 km). The design review underneath shows a predicted apogee and landing speed as you edit.
4. **Auto-tune (optional).** Click Auto-Tune Engine & Chute and the app searches for thrust, propellant, parachute size and deploy altitude that hit your target and land safely.
5. **Launch.** Go to the Launch Simulator tab, pick a speed (1x to 50x) and hit Launch. You get live telemetry, a flight graph and a sky that changes with altitude.
6. **Read the report.** After touchdown you get apogee, top speed, max Q, landing speed and a score out of 100.

## How the sketch becomes a rocket

The sketch reader scans the canvas row by row and records how wide the outline is at each height. From that it works out:

- the body width, using the median width through the middle of the drawing
- where the nose ends, which is the first row that reaches about 90% of the body width
- how curved the nose is, which picks conical, parabolic or ogive for the drag value
- the fins, which are any parts of the outline that stick out past the body

All of it uses one pixel-to-metre scale, so the proportions match what you drew. The body is the outline revolved around the vertical axis. Each fin is the exact flared shape from your drawing, extruded flat and copied around the rocket using the fin count. In the side view it lines up with the sketch.

For the best result, draw a closed, left-right symmetric outline. Use the Spin button to switch between a still side view and a slowly rotating one.

## backend.py (OpenCV prototype)

`backend.py` is a small Python script that does the same sketch analysis with OpenCV. It isn't connected to the web app. `aerocraft.html` runs entirely in the browser and never calls it, so the 3D model and the simulation don't depend on it.

What it does with a sketch image:

1. Blurs the image and runs Canny edge detection.
2. Takes the largest outside contour and fills it in to get a solid silhouette. This works for both filled shapes and thin outlines.
3. Measures the width of the silhouette at every row, then splits it up the same way the browser version does: body width from the middle of the drawing, nose end where the width reaches about 90% of the body, nose shape from how curved the nose is, and fins from rows wider than the body.
4. Converts the pixel measurements to the app's slider values (nose height, body length, body diameter, fin span, nose shape) using one scale for both axes, plus a rough drag coefficient from the same formula the app uses.

If it finds nothing, it returns `{"status": "No valid geometry detected"}`.

To try it:

```
pip install opencv-python numpy
python backend.py              # runs a built-in pencil-rocket test sketch
python backend.py sketch.png   # analyzes your own image
```

Dark lines on a light background (like a scan or photo of paper) are flipped automatically. PNGs with transparency are treated as a mask.

It prints the measurements in pixels and the converted rocket parameters. The outline thickness isn't compensated for the way the browser version does, so results can be a pixel or two wider.

## The physics

Flight is a vertical, one-dimensional simulation using Euler integration at a fixed 20 ms step.

- **Gravity** falls off with altitude (inverse square).
- **Air density** is exponential, 1.225 kg/m3 at sea level with an 8,500 m scale height, and zero above 85 km.
- **Thrust and burn rate** come from engine thrust times the number of engines, and fuel Isp (RP-1 310 s, methane 380 s, hydrogen 450 s). Mass drops as propellant burns.
- **Drag** is `0.5 * rho * v^2 * Cd * A`. Cd comes from the nose shape plus a small fin term, and the parachute adds drag once it opens.
- **Parachute** opens when the rocket is falling and drops below the deploy altitude.
- **Landing** at 8 m/s or faster counts as a crash.

Fast-forward doesn't change the result. The sim always takes the same fixed steps, and the speed setting only decides how many it runs per frame. A 50x flight gives the same numbers as a 1x flight.

## Auto-tune and design review

Both use a headless copy of the same flight physics, with nothing drawn on screen.

Auto-tune is a random hill-climb: 250 tries, each nudging thrust, propellant, parachute size and deploy altitude by up to about 20%, keeping whichever is closest to the target apogee while landing under 7 m/s and lifting off with a thrust-to-weight ratio of at least 1.15. It's a search algorithm, not a machine-learning model, and because it's random, two runs can give slightly different answers.

The design review checks static stability (in calibers), thrust-to-weight, and the predicted apogee and landing speed.

## Score

`100 * (1 - |apogee - target| / target)`, never below 0, and halved if the rocket crashes.

## Known limits

- Flight is straight up and down. There's no wind, steering or sideways motion, so stability is reported but doesn't change the trajectory.
- The body is round, so a sketch matches from the side but not from the front.
- With an odd fin count (like 3), the fins aren't mirrored in the side view. Use 4 or 6 to match the sketch exactly.
- Stages and stage rings are visual only. Staging isn't simulated.
- Mach number uses a fixed speed of sound (340 m/s), and there's no transonic drag.
- `backend.py` isn't wired into the web app yet. Connecting them would need a small server (Flask or FastAPI, for example) that the page sends the canvas image to.
- The sketch reader looks at the outer edges of each row, so inner details and concave notches are ignored. Several strokes on the canvas get merged into one outline.
- Mass, center of mass and center of pressure are simple estimates, good for comparing designs rather than for real engineering.

## Built with

Plain HTML, CSS and JavaScript for the app, [Tailwind CSS](https://tailwindcss.com) (CDN), [Three.js](https://threejs.org) r128 for the 3D view, the Canvas API for the sketchpad, graph and flight view, and the Web Audio API for the launch sound. The `backend.py` prototype uses Python, OpenCV and NumPy.

## Files

- `aerocraft.html`: the whole app
- `backend.py`: standalone OpenCV version of the sketch analysis (not used by the app)
- `README.md`: this file
