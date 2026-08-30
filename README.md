# ⚡ Ion Thruster — Lorentz Simulation

A 2D interactive physics simulation of a gridded ion thruster engine implementing the Lorentz force law in real-time, built in Python using Pygame.

<img width="819" height="617" alt="screen of ion thruster" src="https://github.com/user-attachments/assets/009f3fd3-ec24-487f-9f4c-ebbef0686413" /> 

## 🔬 About the Project

Ion thrusters are a class of spacecraft propulsion systems that accelerate charged particles using electric and magnetic fields to generate thrust. This simulation models the core physics of a **magnetic ion thruster**: charged particles (electrons or Argon ions) are injected from an ionization chamber into an external magnetic field zone, where the **Lorentz force** deflects their trajectories into a curved, directed exhaust beam.

The engine geometry is drawn using `pygame.draw` primitives — ionization chamber body, converging nozzle, and propellant feed lines — making it visually grounded in a real thruster layout.

## ✨ Key Features

- **2D Thruster Body** — ionization chamber, converging nozzle, and propellant feed pipe rendered with pygame geometry
- **Lorentz Force Physics** — particles deflect inside the B-field zone according to $\mathbf{F} = q\mathbf{v} \times \mathbf{B}$; trajectory curvature changes live with slider input
- **Interactive UI Controls:**
  - **B-field slider** — drag to change magnetic field strength in real-time
  - **Injection angle slider** — adjust the particle entry angle (α)
  - **Particle type toggle** — switch between Electron and Argon Ion (different mass and charge)
- **Live Physics Panel** — right-side HUD calculates and displays per-frame:
  - Cyclotron radius $R = mv / (|q|B)$
  - Cyclotron period $T = 2\pi m / (|q|B)$
  - Lorentz force magnitude $F = qvB\sin\alpha$
- **Fading particle trails** — comet-style motion history communicates deflection curvature at a glance

## 📐 Physics Principles

**Lorentz Force Law** — the core equation driving all particle motion:

$$\mathbf{F} = q(\mathbf{v} \times \mathbf{B})$$

With **B** pointing along +Z (into the screen), the 2D cross-product resolves to:

$$F_x = q v_y B, \quad F_y = -q v_x B$$

**Cyclotron Radius** — radius of the circular orbit a charged particle traces in a uniform magnetic field:

$$R = \frac{mv}{|q|B}$$

**Cyclotron Period** — time for one full orbit (independent of particle speed):

$$T = \frac{2\pi m}{|q|B}$$

**Euler Integration** — velocity is updated each frame using Newton's second law:

$$\mathbf{v}_{n+1} = \mathbf{v}_n + \frac{\mathbf{F}}{m} \Delta t$$

## 🛠️ How to Run

1. Install Python 3 and Pygame:
   ```bash
   pip install pygame
   ```

2. Clone the repository and run:
   ```bash
   git clone https://github.com/ulykpanbolekbai/ion-thruster-lorentz-simulation
   cd ion-thruster-lorentz-simulation
   python main.py
   ```

## 🎮 Controls

| Control | Action |
|---------|--------|
| **B-field slider** | Increase / decrease magnetic field strength |
| **Angle slider** | Change particle injection angle α |
| **Type toggle button** | Switch between Electron (−1e) and Argon Ion (+1e) |
| **ESC** | Exit the simulation |

## ⚙️ Tunable Constants

Key parameters defined at the top of `main.py` for quick experimentation:

| Constant | Default | Description |
|----------|---------|-------------|
| `B_FIELD_STRENGTH` | `0.08` | Initial magnetic field strength |
| `PARTICLE_SPEED` | `3.5` | Particle injection speed (px/frame) |
| `MAX_PARTICLES` | `80` | Maximum live particles on screen |
| `SPAWN_INTERVAL_MS` | `100` | Milliseconds between new particle spawns |

## 🧰 Tech Stack

- **Language:** Python 3
- **Graphics:** Pygame
- **Architecture:** Object-Oriented (OOP)
- **Physics Integration:** Euler method (per-frame velocity update)

## 📁 Project Structure

```
main.py
│
├── Configuration constants (B-field, colors, zone layout)
├── Physics core
│   ├── lorentz_force()
│   └── apply_magnetic_force()
├── Calculated quantities
│   ├── calc_radius()     — cyclotron radius R = mv/(|q|B)
│   └── calc_period()     — cyclotron period T = 2πm/(|q|B)
├── UI classes
│   ├── Slider            — draggable parameter control
│   └── ToggleButton      — particle type selector
├── Particle class        — position, velocity, trail, Lorentz update
├── ParticleSystem        — spawn manager and lifecycle controller
└── Rendering functions
    ├── draw_thruster_body()
    ├── draw_field_zone()
    ├── draw_physics_panel()
    └── draw_ui_panel()
```

---

*Developed as a Mechanical / Aerospace Engineering portfolio project.*
