import pygame
from pygame.locals import *
from pygame import mixer #Mixer is for sounds
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60 #So that the game runs at 60 fps regardless of the computer speed

screen_width = 800
screen_height = 800

#This function displays the game window
screen = pygame.display.set_mode((screen_width, screen_height))

#This function sets the title
pygame.display.set_caption("Samy's Parkour")

#Font
font = pygame.font.SysFont("impact", 70)
font_coin = pygame.font.SysFont("copperplate", 30)

#Define game variables
tile_size = 40
game_over = 0
main_menu = True
level = 1
max_levels = 5
coin_collect = 0

#Colors
white = (255, 255, 255)
blue = (0, 0, 255)

#Load Images
bg_image = pygame.image.load("images/bg.png")
restart_img = pygame.image.load("images/restart_btn.png")
start_img = pygame.image.load("images/start_btn.png")
exit_img = pygame.image.load("images/exit_btn.png")

#Load sounds
pygame.mixer.music.load("images/music.wav")
pygame.mixer.music.play(-1, 0.0, 2500) #5000 for delay
coin_fx = pygame.mixer.Sound("images/coin.wav")
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound("images/jump.wav")
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound("images/game_over.wav")
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#To reset level
def reset_level(level):
    player.Reset(100, screen_height - 130)
    #To remove existing things overlapping with ones in the next level
    blob_group.empty()
    platform_group.empty()
    lava_group.empty()
    win_group.empty()

    #Load in level data and create world
    if path.exists(f"level{level}_data"):
        pickle_in = open(f"level{level}_data", "rb") #This is to open the level
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False


        #Get mouse position
        pos = pygame.mouse.get_pos()

        #Check hover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        #Draw button
        screen.blit(self.image, (self.rect))

        return action

class Player(): #The player class is in the "Reset" function
    def __init__(self, x, y):
        self.Reset(x, y)

    def update(self, game_over):
        #dx and dy are for movement in x and y direction
        dx = 0
        dy = 0
        walk_cooldown = 5
        collision_max = 20
        
        if game_over == 0:
            #Get keypresses/control the player
            key=pygame.key.get_pressed()
            if key[pygame.K_UP] and self.jumped == False and self.in_air == False: #self.in_air to prevent multiple jumps
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_UP] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False: #To reset the animation to standing when its not moving
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #For Animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #For Gravity
            self.vel_y += 1 #This means falling
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y
            
            #Check for collision
            self.in_air = True
            for tile in world.tile_list:
                #Check for collision in the x direction/left and right
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #Check for collision in the y direction/up and down
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #Check if below the ground/jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0 #To make his head unstuck
                    #Check if above the ground/falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            #Check for collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                game_over_fx.play()
            
            #Check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()
            
            #Check for collision with win door
            if pygame.sprite.spritecollide(self, win_group, False):
                game_over = 1

            #Check for collision with moving platforms
            for platform in platform_group:
                #Collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #Collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #CHeck if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < collision_max:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #Check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < collision_max:
                        self.rect.bottom = platform.rect.top - 1 #This makes the player kinda floating to avoid stuck
                        dy = 0
                        self.in_air = False
                    #Move sideways with platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            #Update player position
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, white, (screen_width // 2) - 165, screen_height // 2)
            if self.rect.y > 200: #To limit how high the dead player
                self.rect.y -= 5

        #Draw the player on the screen
        screen.blit(self.image, self.rect)

        return game_over
    
    def Reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right=pygame.image.load(f'images/guy{num}.png') #This is to change guy1 through 4
            img_right = pygame.transform.scale(img_right, (35, 70))
            img_left = pygame.transform.flip(img_right, True, False) #This is to flip the image so that when moving left the image mirrors
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('images/ghost.png')
        self.image = self.images_right[self.index] #This is to set the default/standing image of the player
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []
        #Load images
        dirt_img = pygame.image.load('images/dirt.png')
        grass_img = pygame.image.load('images/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    #This is to resize the dirt image to fit the tile size
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    #This is to resize the grass image to fit the tile size
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size - 10, row_count * tile_size + 5)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0) #This one is moving right
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1) #This one is moving up
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    win = Win(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    win_group.add(win)
                col_count +=1
            row_count +=1
    
    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1]) #This is going to take the image and put it in the rectangle's coordinates

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('images/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 20:
            self.move_direction *= -1 #This is to change direction after moving 30 pixels to the right
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size //2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 30:
            self.move_direction *= -1 #This is to change direction after moving 50 pixels to the right
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size *1.5))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Win(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/win.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size * 1.5))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


player = Player(100, screen_height - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
win_group = pygame.sprite.Group()

#Coin icon in top left
screen_coin = Coin(tile_size //2, tile_size //2)
coin_group.add(screen_coin)

#Load in level data and create world
if path.exists(f"level{level}_data"):
    pickle_in = open(f"level{level}_data", "rb")
    world_data = pickle.load(pickle_in)
world = World(world_data)

#For buttons
restart_button = Button(screen_width // 2 - 60, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 300, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 50, screen_height // 2, exit_img)

#The game needs some kind of loop to keep it running
run = True
while run:

    clock.tick(fps)

    #screen.blit is a function that inserts an image onto the screen at a specific location
    screen.blit(bg_image, (0, 0))
    
    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        world.draw()

        if game_over == 0:
            blob_group.update()
            platform_group.update()
            #Update coins collected
            #Check for collision with coins
            if pygame.sprite.spritecollide(player, coin_group, True):
                coin_collect += 1
                coin_fx.play()
            draw_text('Coins collected: ' + str(coin_collect), font_coin, white, tile_size, 5)

        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        win_group.draw(screen)

        game_over = player.update(game_over)
        #If player dies/game over
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level) #To reset the level if the player dies
                game_over = 0
                coin_collect = 0

        #If player wins
        if game_over == 1:
            level += 1
            if level <= max_levels:
                #To reset the level to load the next level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font, white, (screen_width // 2) - 140, screen_height // 2) 
                #Restart game
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    coin_collect = 0

    for event in pygame.event.get():
        if event.type == QUIT:
            run = False
    pygame.display.update()

pygame.quit()