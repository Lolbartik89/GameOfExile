import pygame
import sys
import os
import math
from typing import Tuple

pygame.init()

# ---------------- Window settings ----------------
WIDTH = 1920
HEIGHT = 1080
WINDOW_TITLE = "Game of Exile"
FPS = 60

# Start as windowed; toggling fullscreen will recreate screen
is_fullscreen = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()

# ---------------- Paths ----------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
IMG_DIR = os.path.join(ASSET_DIR, "images")

# ---------------- Load background ----------------
# Ensure you have background_menu.bmp (or change filename)
bg_path = os.path.join(IMG_DIR, "background_menu.bmp")
if not os.path.exists(bg_path):
    raise FileNotFoundError(f"Background not found: {bg_path}")
background_menu = pygame.image.load(bg_path)
background_menu = pygame.transform.scale(background_menu, (WIDTH, HEIGHT))

# ---------------- Fonts & Colors ----------------
font_title = pygame.font.SysFont("serif", 72, bold=True)
font_button = pygame.font.SysFont("serif", 48, bold=True)
font_small = pygame.font.SysFont("serif", 28, bold=False)

GOLD = (255, 215, 0)
NIGHT_BLUE = (15, 30, 70)
BROWN = (139, 69, 19)
DARK_RED = (139, 0, 0)
WHITE = (255, 255, 255)
SEMI_BLACK = (10, 10, 10, 180)

# ---------------- Main menu buttons ----------------
button_start = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 80)
button_exit = pygame.Rect(50, 50, 200, 60)
button_settings = pygame.Rect(WIDTH - 300, 50, 230, 60)

# ---------------- Settings state & UI ----------------
current_menu = "main"  # 'main' or 'settings'

# settings values
music_on = True
volume = 80  # 0..100
fullscreen = is_fullscreen

# panel geometry (center)
PANEL_W = 900
PANEL_H = 700
panel_rect = pygame.Rect((WIDTH - PANEL_W) // 2, (HEIGHT - PANEL_H) // 2, PANEL_W, PANEL_H)

# settings buttons left column (as rects placed inside panel)
left_x = panel_rect.left + 70
item_w = 420
item_h = 70
gap = 24
items = ["Sound", "Graphics", "Controls", "Language"]
item_rects = []
for i in range(len(items)):
    r = pygame.Rect(left_x, panel_rect.top + 120 + i * (item_h + gap), item_w, item_h)
    item_rects.append(r)

# Back button inside panel (right-bottom)
back_button = pygame.Rect(panel_rect.right - 220, panel_rect.bottom - 100, 180, 60)

# volume slider rect (we will draw slider inside sound area)
slider_bar = pygame.Rect(left_x + 430, item_rects[0].centery - 8, 300, 16)
slider_handle_radius = 12
dragging_slider = False

# animation state for panel scale (0..1)
panel_scale = 0.0
panel_anim_speed = 6.0  # larger = faster
animating_open = False
animating_close = False

# helper functions ------------------------------------------------
def draw_button_simple(rect: pygame.Rect, text: str, base_color: Tuple[int,int,int], hover_color: Tuple[int,int,int]):
    """Draw a rectangular button with GOLD text, hover effect handled by color selection."""
    mpos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mpos) else base_color
    pygame.draw.rect(screen, color, rect, border_radius=8)
    txt = font_button.render(text, True, GOLD)
    screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

def draw_main_menu():
    screen.blit(background_menu, (0, 0))
    # Title
    title = font_title.render("GAME OF EXILE", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
    # Buttons
    draw_button_simple(button_start, "START", BROWN, (180, 140, 90))
    draw_button_simple(button_exit, "EXIT", DARK_RED, (180, 50, 50))
    draw_button_simple(button_settings, "SETTINGS", NIGHT_BLUE, (30, 60, 120))

def draw_dim():
    """Draw a semi-transparent dark overlay to dim background."""
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    s.fill((8, 8, 12, 180))
    screen.blit(s, (0, 0))

def draw_settings_panel(scale: float):
    """Draw settings panel scaled from center. scale in (0..1]."""
    # compute scaled rect
    sw = max(10, int(PANEL_W * scale))
    sh = max(10, int(PANEL_H * scale))
    sx = WIDTH // 2 - sw // 2
    sy = HEIGHT // 2 - sh // 2
    panel = pygame.Rect(sx, sy, sw, sh)

    # Panel background (night blue with subtle border)
    pygame.draw.rect(screen, NIGHT_BLUE, panel, border_radius=12)
    pygame.draw.rect(screen, (60, 40, 30), panel, 3, border_radius=12)

    # If scale small, don't draw internal contents (avoid layout mess)
    if scale < 0.3:
        return

    # content coordinates relative to panel
    padding_x = 40
    title_y = panel.top + 30
    # Title
    title = font_title.render("SETTINGS", True, GOLD)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, title_y))

    # Draw left list items with hover
    for idx, name in enumerate(items):
        r = item_rects[idx]
        # scaled rect repositioning: as panel may be scaled, shift them to current panel
        # We'll compute offset between original panel and current panel and apply it
        dx = panel.left - panel_rect.left
        dy = panel.top - panel_rect.top
        rr = pygame.Rect(r.left + dx, r.top + dy, r.width, r.height)

        # hover
        mpos = pygame.mouse.get_pos()
        hover = rr.collidepoint(mpos)
        base_col = (30, 40, 60)
        hov_col = (70, 50, 120)  # slightly lighter
        pygame.draw.rect(screen, hov_col if hover else base_col, rr, border_radius=8)
        # label
        lbl = font_button.render(name, True, GOLD)
        screen.blit(lbl, (rr.left + 12, rr.centery - lbl.get_height() // 2))

        # special content for Sound item (volume + music toggle)
        if name == "Sound":
            # music ON/OFF small button
            music_rect = pygame.Rect(rr.right - 140, rr.centery - 20, 120, 40)
            pygame.draw.rect(screen, (40, 40, 40), music_rect, border_radius=6)
            music_txt = font_small.render("ON" if music_on else "OFF", True, GOLD)
            screen.blit(music_txt, (music_rect.centerx - music_txt.get_width()//2,
                                     music_rect.centery - music_txt.get_height()//2))
            # volume bar (draw on same panel coordinates)
            sbar = pygame.Rect(slider_bar.left + dx, slider_bar.top + dy, slider_bar.width, slider_bar.height)
            pygame.draw.rect(screen, (80, 80, 80), sbar, border_radius=8)
            # filled portion
            fill_w = int((volume / 100.0) * sbar.width)
            pygame.draw.rect(screen, GOLD, (sbar.left, sbar.top, fill_w, sbar.height), border_radius=8)
            # handle
            handle_x = sbar.left + fill_w
            pygame.draw.circle(screen, (220, 180, 140), (handle_x, sbar.centery), slider_handle_radius)

        # special content for Graphics item (fullscreen toggle display)
        if name == "Graphics":
            gfx_rect = pygame.Rect(rr.right - 215, rr.centery - 20, 220, 40)
            pygame.draw.rect(screen, (40, 40, 40), gfx_rect, border_radius=6)
            gfx_txt = font_small.render("Fullscreen: " + ("ON" if fullscreen else "OFF"), True, GOLD)
            screen.blit(gfx_txt, (gfx_rect.left + 10, gfx_rect.centery - gfx_txt.get_height()//2))

        # Controls & Language labels
        if name == "Controls":
            c_txt = font_small.render("View controls", True, WHITE)
            screen.blit(c_txt, (rr.left + 200, rr.centery - c_txt.get_height()//2))
        if name == "Language":
            l_txt = font_small.render("English", True, WHITE)
            screen.blit(l_txt, (rr.left + 300, rr.centery - l_txt.get_height()//2))

    # Draw Back button inside panel (right-bottom)
    brect = pygame.Rect(back_button.left + (panel.left - panel_rect.left),
                        back_button.top + (panel.top - panel_rect.top),
                        back_button.width, back_button.height)
    mpos = pygame.mouse.get_pos()
    bhover = brect.collidepoint(mpos)
    pygame.draw.rect(screen, (90, 40, 10) if not bhover else (140, 80, 30), brect, border_radius=8)
    back_txt = font_button.render("BACK", True, GOLD)
    screen.blit(back_txt, (brect.centerx - back_txt.get_width()//2, brect.centery - back_txt.get_height()//2))

# ---------- Event handling helpers ----------
def point_in_scaled_item(idx):
    """Return True if mouse is inside scaled item idx (taking animation offsets into account)."""
    # compute current scaled panel top-left
    sw = max(1, int(PANEL_W * panel_scale))
    sh = max(1, int(PANEL_H * panel_scale))
    dx = WIDTH // 2 - sw // 2 - panel_rect.left
    dy = HEIGHT // 2 - sh // 2 - panel_rect.top
    rr = item_rects[idx].copy()
    rr.left += dx
    rr.top += dy
    return rr.collidepoint(pygame.mouse.get_pos())

def point_in_scaled_back():
    sw = max(1, int(PANEL_W * panel_scale))
    sh = max(1, int(PANEL_H * panel_scale))
    dx = WIDTH // 2 - sw // 2 - panel_rect.left
    dy = HEIGHT // 2 - sh // 2 - panel_rect.top
    rr = back_button.copy()
    rr.left += dx
    rr.top += dy
    return rr.collidepoint(pygame.mouse.get_pos())

def handle_settings_mouse_down(pos):
    global music_on, volume, fullscreen, is_fullscreen, current_menu, animating_close, animating_open, dragging_slider
    # clicks on scaled items
    if panel_scale < 0.3:
        return
    # check sound music button
    # compute scaled rects same as draw
    for idx, name in enumerate(items):
        # check click inside scaled item
        if point_in_scaled_item(idx):
            if name == "Sound":
                # music toggle zone (approx)
                sw = max(1, int(PANEL_W * panel_scale))
                dx = WIDTH // 2 - sw // 2 - panel_rect.left
                dy = HEIGHT // 2 - int(PANEL_H * panel_scale) // 2 - panel_rect.top
                music_rect = pygame.Rect(item_rects[idx].right + dx - 140, item_rects[idx].centery + dy - 20, 120, 40)
                # if clicked near music rect toggle
                if music_rect.collidepoint(pos):
                    music_on = not music_on
                    print("Music toggled:", music_on)
                    return
                # check slider bar zone
                sbar = pygame.Rect(slider_bar.left + dx, slider_bar.top + dy, slider_bar.width, slider_bar.height)
                if sbar.collidepoint(pos):
                    # start dragging
                    dragging_slider = True
                    # set volume based on pos
                    rel = pos[0] - sbar.left
                    vol = int(max(0, min(1, rel / sbar.width)) * 100)
                    set_volume(vol)
                    return
            if name == "Graphics":
                # toggle fullscreen by clicking on the item rect area (simple)
                fullscreen = not fullscreen
                toggle_fullscreen(fullscreen)
                print("Fullscreen:", fullscreen)
                return
            if name == "Controls":
                print("Controls clicked (placeholder)")
                return
            if name == "Language":
                print("Language clicked (placeholder)")
                return
    # Check back button
    if point_in_scaled_back():
        # start closing animation
        start_close_settings()
        return

def set_volume(v: int):
    global volume
    volume = max(0, min(100, int(v)))
    print("Volume set to", volume)
    # here you could call pygame.mixer.music.set_volume(volume/100.0) if using music

def toggle_fullscreen(flag: bool):
    global screen, is_fullscreen
    is_fullscreen = flag
    if is_fullscreen:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    print("Toggled fullscreen:", is_fullscreen)

def start_open_settings():
    global current_menu, panel_scale, animating_open, animating_close
    current_menu = "settings"
    panel_scale = 0.0
    animating_open = True
    animating_close = False

def start_close_settings():
    global animating_close, animating_open
    animating_close = True
    animating_open = False

# ---------------- Main loop ----------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0  # seconds
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Basic main menu interactions
        if current_menu == "main":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mpos = event.pos
                if button_start.collidepoint(mpos):
                    print("Start button clicked!")
                if button_exit.collidepoint(mpos):
                    running = False
                if button_settings.collidepoint(mpos):
                    start_open_settings()

        # Settings menu interactions
        if current_menu == "settings":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_settings_mouse_down(event.pos)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # stop dragging slider
                dragging_slider = False
            if event.type == pygame.MOUSEMOTION and dragging_slider:
                # update volume while dragging
                # compute scaled sbar rect
                sw = max(1, int(PANEL_W * panel_scale))
                dx = WIDTH // 2 - sw // 2 - panel_rect.left
                dy = HEIGHT // 2 - int(PANEL_H * panel_scale) // 2 - panel_rect.top
                sbar = pygame.Rect(slider_bar.left + dx, slider_bar.top + dy, slider_bar.width, slider_bar.height)
                rel = event.pos[0] - sbar.left
                vol = int(max(0, min(1, rel / sbar.width)) * 100)
                set_volume(vol)

    # update animations
    if current_menu == "settings" and animating_open:
        panel_scale += panel_anim_speed * dt
        if panel_scale >= 1.0:
            panel_scale = 1.0
            animating_open = False
    if current_menu == "settings" and animating_close:
        panel_scale -= panel_anim_speed * dt
        if panel_scale <= 0.0:
            panel_scale = 0.0
            animating_close = False
            current_menu = "main"

    # draw
    screen.blit(background_menu, (0, 0))
    if current_menu == "main":
        # draw main menu
        draw_main_menu()
    elif current_menu == "settings":
        # dim background and draw panel scaled
        draw_dim()
        draw_settings_panel(panel_scale)

    pygame.display.flip()

pygame.quit()
sys.exit()
