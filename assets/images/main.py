import pygame
import random
import time

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Catch the Square")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLASH = (255, 255, 0)

try:
    click_sound = pygame.mixer.Sound("click.wav")
except:
    click_sound = None

square_size = 50
square_x = random.randint(0, 800 - square_size)
square_y = random.randint(0, 600 - square_size)
square_color = (255, 0, 0)
score = 0
font = pygame.font.SysFont(None, 36)
time_limit = 30
start_time = time.time()
flash_time = 0
game_over = False

def draw_square():
    pygame.draw.rect(screen, square_color, (square_x, square_y, square_size, square_size))

def draw_score():
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

def draw_timer():
    time_left = max(0, int(time_limit - (time.time() - start_time)))
    timer_text = font.render(f"Time: {time_left}", True, BLACK)
    screen.blit(timer_text, (680, 10))

def move_square():
    global square_x, square_y
    square_x = random.randint(0, 800 - square_size)
    square_y = random.randint(0, 600 - square_size)

def is_square_clicked(mouse_pos):
    mouse_x, mouse_y = mouse_pos
    return square_x <= mouse_x <= square_x + square_size and square_y <= mouse_y <= square_y + square_size

def game_over_screen():
    screen.fill(WHITE)
    over_text = font.render(f"Game Over! Score: {score}", True, BLACK)
    restart_text = font.render("Click to restart", True, BLACK)
    screen.blit(over_text, (250, 250))
    screen.blit(restart_text, (250, 300))
    pygame.display.flip()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                score = 0
                start_time = time.time()
                game_over = False
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and is_square_clicked(event.pos):
                if click_sound:
                    click_sound.play()
                score += 1
                move_square()
                flash_time = time.time()

    if not game_over:
        if time.time() - start_time > time_limit:
            game_over = True

        screen.fill(FLASH if time.time() - flash_time < 0.1 else WHITE)
        draw_square()
        draw_score()
        draw_timer()
        pygame.display.flip()
    else:
        game_over_screen()

pygame.quit()