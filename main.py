import pygame
import math
import random

WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 600
FPS           = 60
WINDOW_TITLE  = "Lorentz Ion Thruster Simulation"

COLOR_BG           = (10,  12,  20)
COLOR_FIELD_BORDER = (40,  80, 160)
COLOR_ION          = (255, 200,  50)
COLOR_ELECTRON     = ( 80, 200, 255)
COLOR_TEXT         = (200, 210, 230)
COLOR_ACCENT       = ( 60, 180, 120)
COLOR_THRUSTER     = (120, 130, 150)
COLOR_NOZZLE_GLOW  = (255, 140,  30)
COLOR_SLIDER_BG    = ( 30,  35,  50)
COLOR_SLIDER_FILL  = ( 60, 120, 200)
COLOR_SLIDER_KNOB  = (200, 220, 255)
COLOR_PANEL_BG     = ( 15,  18,  30)

# Particle type definitions — mass and charge scaled for screen simulation
PARTICLE_TYPES = {
    "Electron":   {"mass": 0.05,  "charge": -1.0, "colour": COLOR_ELECTRON},
    "Argon Ion":  {"mass": 1.0,   "charge":  1.0, "colour": COLOR_ION},
}

TIME_STEP          =  1.0
PARTICLE_SPEED     =  3.5

MAX_PARTICLES      = 80
SPAWN_INTERVAL_MS  = 100

# Field zone starts right after the thruster nozzle
FIELD_ZONE_X      = 220
FIELD_ZONE_Y      = 80
FIELD_ZONE_WIDTH  = 340
FIELD_ZONE_HEIGHT = 440


def lorentz_force(charge, speed, b_field, alpha_rad):
    # F = q * v * B * sin(alpha)
    return charge * speed * b_field * math.sin(alpha_rad)


def apply_magnetic_force(vx, vy, charge, b_field, mass, dt):
    # B into the screen along Z; cross product gives Fx = q*vy*B, Fy = -q*vx*B
    fx =  charge * vy * b_field
    fy = -charge * vx * b_field
    return vx + (fx / mass) * dt, vy + (fy / mass) * dt


def calc_radius(mass, speed, charge, b_field):
    # Cyclotron radius: R = m*v / (|q|*B)
    if abs(charge) < 1e-9 or abs(b_field) < 1e-9:
        return float("inf")
    return (mass * speed) / (abs(charge) * b_field)


def calc_period(mass, charge, b_field):
    # Cyclotron period: T = 2*pi*m / (|q|*B)
    if abs(charge) < 1e-9 or abs(b_field) < 1e-9:
        return float("inf")
    return (2 * math.pi * mass) / (abs(charge) * b_field)


class Slider:
    """A horizontal drag slider. Call handle_event() then draw() each frame."""

    def __init__(self, x, y, w, label, val_min, val_max, initial):
        self.rect    = pygame.Rect(x, y, w, 6)
        self.label   = label
        self.min     = val_min
        self.max     = val_max
        self.value   = initial
        self.dragging = False
        self.knob_r  = 8

    def _knob_x(self):
        t = (self.value - self.min) / (self.max - self.min)
        return int(self.rect.x + t * self.rect.width)

    def handle_event(self, event):
        # Only process mouse events — other event types don't have .pos
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            return

        kx = self._knob_x()
        ky = self.rect.centery
        knob_hit = math.hypot(event.pos[0] - kx, event.pos[1] - ky) <= self.knob_r + 4

        if event.type == pygame.MOUSEBUTTONDOWN and knob_hit:
            self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            rel = (event.pos[0] - self.rect.x) / self.rect.width
            self.value = max(self.min, min(self.max, self.min + rel * (self.max - self.min)))

    def draw(self, surface, font):
        # Track
        pygame.draw.rect(surface, COLOR_SLIDER_BG,
                         (self.rect.x, self.rect.y - 2, self.rect.width, self.rect.height + 4), border_radius=3)
        # Fill up to knob
        fill_w = self._knob_x() - self.rect.x
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_SLIDER_FILL,
                             (self.rect.x, self.rect.y - 2, fill_w, self.rect.height + 4), border_radius=3)
        # Knob
        pygame.draw.circle(surface, COLOR_SLIDER_KNOB, (self._knob_x(), self.rect.centery), self.knob_r)
        # Label and current value
        txt = font.render(f"{self.label}: {self.value:.3f}", True, COLOR_TEXT)
        surface.blit(txt, (self.rect.x, self.rect.y - 20))


class ToggleButton:
    """Cycles through a list of string options on each click."""

    def __init__(self, x, y, w, h, options):
        self.rect    = pygame.Rect(x, y, w, h)
        self.options = options
        self.index   = 0

    @property
    def value(self):
        return self.options[self.index]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.index = (self.index + 1) % len(self.options)

    def draw(self, surface, font):
        pygame.draw.rect(surface, COLOR_SLIDER_FILL, self.rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_SLIDER_KNOB, self.rect, 1, border_radius=5)
        label = font.render(f"Type: {self.value}  ▶", True, COLOR_TEXT)
        surface.blit(label, (self.rect.x + 8, self.rect.y + 6))


class Particle:
    TRAIL_LENGTH = 35

    def __init__(self, ptype, b_field, angle_deg):
        props = PARTICLE_TYPES[ptype]
        self.mass   = props["mass"]
        self.charge = props["charge"]
        self.colour = props["colour"]
        self.ptype  = ptype

        # Spawn at the nozzle exit point
        self.x = float(FIELD_ZONE_X)
        self.y = float(WINDOW_HEIGHT // 2 + random.randint(-15, 15))

        # Velocity direction set by the injection angle slider
        angle_rad = math.radians(angle_deg)
        self.vx = PARTICLE_SPEED * math.cos(angle_rad)
        self.vy = PARTICLE_SPEED * math.sin(angle_rad)

        self.in_field = False
        self.trail    = []
        self.alive    = True

    def update(self, field_rect, b_field, dt):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > self.TRAIL_LENGTH:
            self.trail.pop(0)

        self.in_field = field_rect.collidepoint(self.x, self.y)
        if self.in_field:
            self.vx, self.vy = apply_magnetic_force(
                self.vx, self.vy, self.charge, b_field, self.mass, dt)

        self.x += self.vx * dt
        self.y += self.vy * dt

        if (self.x < -10 or self.x > WINDOW_WIDTH + 10 or
                self.y < -10 or self.y > WINDOW_HEIGHT + 10):
            self.alive = False

    def draw(self, surface):
        trail_len = len(self.trail)
        for i, pos in enumerate(self.trail):
            t      = i / max(trail_len - 1, 1)
            alpha  = int(15 + t * 165)
            radius = max(1, int(1 + t * 2))
            blend  = alpha / 255
            r = int(COLOR_BG[0] * (1 - blend) + self.colour[0] * blend)
            g = int(COLOR_BG[1] * (1 - blend) + self.colour[1] * blend)
            b = int(COLOR_BG[2] * (1 - blend) + self.colour[2] * blend)
            pygame.draw.circle(surface, (r, g, b), pos, radius)

        pygame.draw.circle(surface, self.colour, (int(self.x), int(self.y)), 4)

        speed = math.hypot(self.vx, self.vy)
        if speed > 0:
            nx, ny = self.vx / speed, self.vy / speed
            pygame.draw.line(surface, COLOR_ACCENT,
                             (int(self.x), int(self.y)),
                             (int(self.x + nx * 10), int(self.y + ny * 10)), 1)


class ParticleSystem:
    def __init__(self):
        self.particles    = []
        self._timer       = 0
        self._type_index  = 0

    def update(self, field_rect, b_field, dt, delta_ms, ptype, angle_deg):
        for p in self.particles:
            p.update(field_rect, b_field, dt)
        self.particles = [p for p in self.particles if p.alive]

        self._timer += delta_ms
        if self._timer >= SPAWN_INTERVAL_MS and len(self.particles) < MAX_PARTICLES:
            self.particles.append(Particle(ptype, b_field, angle_deg))
            self._timer = 0

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    @property
    def count(self):
        return len(self.particles)


def draw_thruster_body(surface):
    # Ionization chamber — rectangular housing on the left edge
    chamber_x, chamber_y, chamber_w, chamber_h = 30, 220, 90, 160
    pygame.draw.rect(surface, COLOR_THRUSTER,
                     (chamber_x, chamber_y, chamber_w, chamber_h), 0, border_radius=4)
    pygame.draw.rect(surface, (180, 190, 210),
                     (chamber_x, chamber_y, chamber_w, chamber_h), 2, border_radius=4)

    # Internal electrode lines — visual detail inside the chamber
    for i in range(3):
        ey = chamber_y + 30 + i * 45
        pygame.draw.line(surface, (60, 70, 90),
                         (chamber_x + 8, ey), (chamber_x + chamber_w - 8, ey), 2)

    # Label inside chamber
    font_tiny = pygame.font.SysFont("consolas", 11)
    lbl = font_tiny.render("CHAMBER", True, (80, 90, 110))
    surface.blit(lbl, (chamber_x + 10, chamber_y + 6))

    # Converging nozzle — trapezoid pointing right toward the field zone
    nozzle_points = [
        (chamber_x + chamber_w,     chamber_y + 30),   # top-left of nozzle
        (FIELD_ZONE_X - 2,          WINDOW_HEIGHT // 2 - 18),  # top-right (narrow)
        (FIELD_ZONE_X - 2,          WINDOW_HEIGHT // 2 + 18),  # bottom-right (narrow)
        (chamber_x + chamber_w,     chamber_y + chamber_h - 30),  # bottom-left
    ]
    pygame.draw.polygon(surface, COLOR_THRUSTER, nozzle_points)
    pygame.draw.polygon(surface, (180, 190, 210), nozzle_points, 2)

    # Nozzle exit glow — glowing ring where particles emerge
    glow_x = FIELD_ZONE_X - 2
    glow_y = WINDOW_HEIGHT // 2
    for radius in range(14, 4, -3):
        alpha_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        glow_alpha = int(60 * (1 - radius / 14))
        pygame.draw.circle(alpha_surf, (*COLOR_NOZZLE_GLOW, glow_alpha),
                           (radius, radius), radius)
        surface.blit(alpha_surf, (glow_x - radius, glow_y - radius))

    pygame.draw.circle(surface, COLOR_NOZZLE_GLOW, (glow_x, glow_y), 5)

    # Propellant feed line — pipe coming from the top into the chamber
    pipe_x = chamber_x + chamber_w // 2
    pygame.draw.line(surface, COLOR_THRUSTER, (pipe_x, 0), (pipe_x, chamber_y), 4)
    pygame.draw.line(surface, (180, 190, 210), (pipe_x, 0), (pipe_x, chamber_y), 1)
    lbl2 = font_tiny.render("PROPELLANT", True, (80, 90, 110))
    surface.blit(lbl2, (pipe_x - 35, 10))

    # Power supply lines — two wires going off the bottom of the chamber
    for offset in (-20, 20):
        wx = chamber_x + chamber_w // 2 + offset
        pygame.draw.line(surface, (80, 100, 60),
                         (wx, chamber_y + chamber_h), (wx, WINDOW_HEIGHT), 3)
    lbl3 = font_tiny.render("POWER", True, (80, 90, 110))
    surface.blit(lbl3, (chamber_x + 28, WINDOW_HEIGHT - 16))


def draw_field_zone(surface, rect, b_field):
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((20, 60, 120, 50))
    surface.blit(overlay, (rect.x, rect.y))
    pygame.draw.rect(surface, COLOR_FIELD_BORDER, rect, 2)

    font_tiny = pygame.font.SysFont("consolas", 12)
    lbl = font_tiny.render(f"B-field  ⊗  {b_field:.3f} T", True, COLOR_FIELD_BORDER)
    surface.blit(lbl, (rect.x + 6, rect.y + 6))

    # Dot grid — represents field lines going into the page
    for gx in range(rect.x + 25, rect.x + rect.width, 42):
        for gy in range(rect.y + 32, rect.y + rect.height, 42):
            pygame.draw.circle(surface, COLOR_FIELD_BORDER, (gx, gy), 2)


def draw_physics_panel(surface, font, b_field, ptype, angle_deg, particle_count, fps):
    # Right-side panel background
    panel_x = FIELD_ZONE_X + FIELD_ZONE_WIDTH + 12
    panel_w = WINDOW_WIDTH - panel_x - 8
    pygame.draw.rect(surface, COLOR_PANEL_BG,
                     (panel_x - 6, 6, panel_w + 6, WINDOW_HEIGHT - 12), border_radius=6)
    pygame.draw.rect(surface, COLOR_FIELD_BORDER,
                     (panel_x - 6, 6, panel_w + 6, WINDOW_HEIGHT - 12), 1, border_radius=6)

    props = PARTICLE_TYPES[ptype]
    mass   = props["mass"]
    charge = props["charge"]
    speed  = PARTICLE_SPEED

    # Real-time cyclotron radius and period from current slider values
    R = calc_radius(mass, speed, charge, b_field)
    T = calc_period(mass, charge, b_field)

    angle_rad = math.radians(angle_deg)
    Fx = lorentz_force(abs(charge), speed, b_field, math.pi / 2)

    lines = [
        ("LIVE DATA",        None,        (100, 150, 220)),
        ("",                 None,        COLOR_TEXT),
        ("Particle",         ptype,       COLOR_ION if charge > 0 else COLOR_ELECTRON),
        ("Mass  m",          f"{mass:.3f} u",    COLOR_TEXT),
        ("Charge q",         f"{charge:+.1f} e", COLOR_TEXT),
        ("Speed  v",         f"{speed:.2f} px/f",COLOR_TEXT),
        ("Angle  α",         f"{angle_deg:.1f}°",COLOR_TEXT),
        ("",                 None,        COLOR_TEXT),
        ("CALCULATED",       None,        (100, 150, 220)),
        ("",                 None,        COLOR_TEXT),
        ("Radius R",         f"{R:.2f} px" if R != float("inf") else "∞", COLOR_ACCENT),
        ("Period T",         f"{T:.2f} fr" if T != float("inf") else "∞", COLOR_ACCENT),
        ("Force  F",         f"{Fx:.4f}",  COLOR_ACCENT),
        ("",                 None,        COLOR_TEXT),
        ("STATUS",           None,        (100, 150, 220)),
        ("",                 None,        COLOR_TEXT),
        ("Particles",        str(particle_count), COLOR_TEXT),
        ("FPS",              f"{fps:.0f}", COLOR_TEXT),
    ]

    y = 20
    for key, val, colour in lines:
        if key == "" :
            y += 6
            continue
        if val is None:
            # Section header
            txt = font.render(key, True, colour)
            surface.blit(txt, (panel_x, y))
            pygame.draw.line(surface, colour,
                             (panel_x, y + 16), (panel_x + panel_w - 10, y + 16), 1)
            y += 22
        else:
            k_surf = font.render(key, True, (140, 150, 170))
            v_surf = font.render(val, True, colour)
            surface.blit(k_surf, (panel_x, y))
            surface.blit(v_surf, (panel_x + 68, y))
            y += 18


def draw_ui_panel(surface, font, sliders, toggle):
    # Bottom control bar background
    bar_y  = WINDOW_HEIGHT - 70
    bar_h  = 68
    pygame.draw.rect(surface, COLOR_PANEL_BG, (0, bar_y, FIELD_ZONE_X + FIELD_ZONE_WIDTH, bar_h))
    pygame.draw.line(surface, COLOR_FIELD_BORDER,
                     (0, bar_y), (FIELD_ZONE_X + FIELD_ZONE_WIDTH, bar_y), 1)

    for s in sliders:
        s.draw(surface, font)
    toggle.draw(surface, font)


def main():
    pygame.init()
    screen   = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    font     = pygame.font.SysFont("consolas", 13)
    ticker   = pygame.time.Clock()

    # UI controls — positioned in the bottom bar
    bar_y = WINDOW_HEIGHT - 55
    slider_b     = Slider(40,  bar_y, 130, "B-field", 0.01, 0.30, 0.08)
    slider_angle = Slider(220, bar_y, 130, "Angle °", -30,  30,   0.0)
    toggle_type  = ToggleButton(400, bar_y - 10, 140, 28, list(PARTICLE_TYPES.keys()))

    sliders = [slider_b, slider_angle]

    field_rect = pygame.Rect(FIELD_ZONE_X, FIELD_ZONE_Y, FIELD_ZONE_WIDTH, FIELD_ZONE_HEIGHT)
    particles  = ParticleSystem()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            for s in sliders:
                s.handle_event(event)
            toggle_type.handle_event(event)

        delta_ms = ticker.tick(FPS)

        # Read live slider values each frame
        b_field   = slider_b.value
        angle_deg = slider_angle.value
        ptype     = toggle_type.value

        particles.update(field_rect, b_field, TIME_STEP, delta_ms, ptype, angle_deg)

        screen.fill(COLOR_BG)
        draw_thruster_body(screen)
        draw_field_zone(screen, field_rect, b_field)
        particles.draw(screen)
        draw_physics_panel(screen, font, b_field, ptype, angle_deg,
                           particles.count, ticker.get_fps())
        draw_ui_panel(screen, font, sliders, toggle_type)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main() 