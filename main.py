import pygame
import sys
import math
import copy

# DESCRIPTION:
"""
BE CAREFUL, OR YOU MIGHT CAUSE A TIME PARADOX.
"""

# Initialize pygame
pygame.init()

# Set window size
WIDTH, HEIGHT = 540, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Fifth Echo")

screenName = 'HOME'

data = [[[999 for x in range(30)] for y in range(30)] for z in range(4)]
end = [[0, 0], [0, 0], [0, 0], [0, 0]]

class Player:
    def __init__(self, x, y, color, p_type, frames=[]):
        self.orig = [x, y]

        self.frame_counter = 0
        self.color = color

        self.max_xvel = 0.25
        self.max_yvel = 0.5
        self.accel = 0.05

        # 0 IF PLAYER CONTROLLED, 1 IF GHOST
        self.ptype = p_type

        self.frame_tracker = frames
        self.lives = 1.5

        self.finished = False

        self.reset()

    def get_copy_of_self(self):
        if self.ptype == 0:
            return Player(self.orig[0], self.orig[1], self.color, 1, copy.deepcopy(self.frame_tracker))
        
        else:
            return Player(self.orig[0], self.orig[1], self.color, 1, copy.deepcopy(self.frame_tracker))

    def reset(self):
        self.x = self.orig[0]
        self.y = self.orig[1]
        self.x_vel = 0
        self.y_vel = 0
        self.frame = 0

        self.lives -= 0.5
        
        if self.lives == 0:
            global screenName
            screenName = 'PLAYER_DIED'

    def jump(self, power):
        self.y_vel = -1 * power

    def update(self, pressed, dir, level):
        if not self.finished:
            # Horizontal movement and collision
            if pressed:
                self.x_vel += self.accel * dir
                self.x_vel = max(-self.max_xvel, min(self.x_vel, self.max_xvel))
            else:
                if abs(self.x_vel) >= 0.1:
                    self.x_vel -= 0.1 * (1 if self.x_vel > 0 else -1)
                else:
                    self.x_vel = 0
                    self.frame = 0

            new_x = self.x + self.x_vel
            top_y = int(self.y)
            bottom_y = int(self.y + 0.9)

            if self.x_vel > 0:
                right_x = int(new_x + 0.9)
                if right_x > 29:
                    right_x = 29
                if is_solid(data[level][top_y][right_x]) or is_solid(data[level][bottom_y][right_x]):
                    if is_spike(data[level][top_y][right_x]) or is_spike(data[level][bottom_y][right_x]):
                        self.reset()
                        return None
                    
                    else:
                        self.x = right_x - 1
                        self.x_vel = 0
                else:
                    self.x = new_x
            elif self.x_vel < 0:
                left_x = int(new_x)
                if left_x < 0:
                    left_x = 0
                if is_solid(data[level][top_y][left_x]) or is_solid(data[level][bottom_y][left_x]):
                    if is_spike(data[level][top_y][left_x]) or is_spike(data[level][bottom_y][left_x]):
                        self.reset()
                        return None
                    
                    else:
                        self.x = left_x + 1
                        self.x_vel = 0
                else:
                    self.x = new_x

            # Clamp horizontal position
            self.x = max(0, min(self.x, 29))

            if abs(self.x_vel) >= 0.1:
                self.frame = (self.frame + 1) % 2

            # Apply gravity if not on ground
            below_y = int(self.y + 1)
            left_x = int(self.x)
            right_x = int(self.x + 0.9)

            left_block = data[level][below_y][left_x] if 0 <= below_y < 30 and 0 <= left_x < 30 else 999
            right_block = data[level][below_y][right_x] if 0 <= below_y < 30 and 0 <= right_x < 30 else 999

            self.on_ground = is_solid(left_block) or is_solid(right_block)
            if is_spike(left_block) or is_spike(right_block):
                    self.reset()
                    return None

            if not self.on_ground:
                if self.y_vel < self.max_yvel:
                    self.y_vel += gravity

            # Vertical movement and collision
            new_y = self.y + self.y_vel

            if self.y_vel < 0:
                # Moving up: check head collision
                head_y = int(new_y)
                left_x = int(self.x)
                right_x = int(self.x + 0.9)

                top_left_block = data[level][head_y][left_x] if 0 <= head_y < 30 and 0 <= left_x < 30 else 999
                top_right_block = data[level][head_y][right_x] if 0 <= head_y < 30 and 0 <= right_x < 30 else 999

                if is_solid(top_left_block) or is_solid(top_right_block):
                    if is_spike(top_left_block) or is_spike(top_right_block):
                        self.reset()
                        return None
                    
                    else:
                        self.y = head_y + 1
                        self.y_vel = 0
                else:
                    self.y = new_y

            else:
                # Moving down or stationary: check feet collision
                feet_y = int(new_y + 1)
                left_x = int(self.x)
                right_x = int(self.x + 0.9)

                left_block = data[level][feet_y][left_x] if 0 <= feet_y < 30 and 0 <= left_x < 30 else 999
                right_block = data[level][feet_y][right_x] if 0 <= feet_y < 30 and 0 <= right_x < 30 else 999

                if is_solid(left_block) or is_solid(right_block):
                    if is_spike(left_block) or is_spike(right_block):
                        self.reset()
                        return None
                    
                    else:
                        self.y = feet_y - 1
                        self.y_vel = 0
                        self.on_ground = True
                else:
                    self.y = new_y
                    self.on_ground = False

            self.frame_tracker.append([self.frame, self.x, self.y, self.lives])

            if is_flag(self.x, self.y, level) or is_flag(self.x + 1, self.y, level) or is_flag(self.x, self.y + 1, level) or is_flag(self.x + 1, self.y + 1, level):
                self.finished = True

                self.x = end[level][1]
                self.y = end[level][0]

                for x in range(0, 1801):
                    self.frame_tracker.append([0, end[level][1], end[level][0], self.lives])

    def update_existing(self, level):
        self.frame = self.frame_tracker[self.frame_counter][0]
        self.x = self.frame_tracker[self.frame_counter][1]
        self.y = self.frame_tracker[self.frame_counter][2]
        self.lives = self.frame_tracker[self.frame_counter][3]

        if is_flag(self.x, self.y, level) or is_flag(self.x + 1, self.y, level) or is_flag(self.x, self.y + 1, level) or is_flag(self.x + 1, self.y + 1, level):
            self.finished = True

        self.frame_counter += 1

    def render(self, surface):
        if not self.finished:
            # RENDER CHARACTER
            img_path = f'Assets/Characters/{self.color}{self.frame}.png'
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (18, 18))

            px = int(self.x * 18)
            py = int(self.y * 18)

            surface.blit(img, (px, py))

            # RENDER LIVES
            if self.lives == 1:
                render_image_blocks(f'Assets/Tiles/tile_0044.png', 1, 1, self.x, self.y - 1.5, surface)

            elif self.lives == 0.5:
                render_image_blocks(f'Assets/Tiles/tile_0045.png', 1, 1, self.x, self.y - 1.5, surface)

            else:
                render_image_blocks(f'Assets/Tiles/tile_0046.png', 1, 1, self.x, self.y - 1.5, surface)

            font = pygame.font.SysFont(None, 20)
            label = "You" if self.ptype == 0 else "Past Copy"
            text_surface = font.render(label, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(px + 9, py - 35))  # Centered above the player sprite
            surface.blit(text_surface, text_rect)

    def get_frame_tracker(self):
        return self.frame_tracker

class Enemy:
    def __init__(self, e_type, y, x1, x2):
        self.etype = e_type
        self.y = y
        self.x1 = x1
        self.x2 = x2

def rectangles_overlap(x1, y1, x2, y2):
    width, height = 1, 1
    
    # Check if one rectangle is to the left of the other
    if x1 + width <= x2 or x2 + width <= x1:
        return False
    
    # Check if one rectangle is above the other
    if y1 + height <= y2 or y2 + height <= y1:
        return False
    
    # If neither of the above, they overlap
    return True

def check_finished():
    for player in players:
        if not player.finished:
            return False
        
    return True

def render_image_blocks(path, sizex, sizey, x, y, surface):
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (sizex * 18, sizey * 18))

    px = int(x * 18)
    py = int(y * 18)

    surface.blit(img, (px, py))

def render_image_pixels(path, sizex, sizey, x, y, surface):
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (sizex, sizey))

    px = int(x)
    py = int(y)

    surface.blit(img, (px, py))

def is_solid(tile):
    return not tile in [999, 88, 87, 85, 27, 67]

def is_spike(tile):
    return tile == 68

def is_flag(x, y, level):
    flag_x = end[level][1]
    flag_y = end[level][0]

    return flag_x <= x <= flag_x + 1 and flag_y <= y <= flag_y + 1

def touching_spike(px, py, level):
    for y_idx, row in enumerate(data[level]):
        for x_idx, tile in enumerate(row):
            if tile == 68:
                if x_idx <= px < x_idx + 1 and y_idx <= py < y_idx + 1:
                    return True
    return False

def testPlatforms():
    # 1. Single block (1×1)
    buildPlatform(0, 5, 5, 5, 5)

    # 2. Single column (1×n)
    buildPlatform(0, 10, 10, 5, 7)  # 3 blocks tall

    # 3. Single row (n×1)
    buildPlatform(0, 15, 17, 5, 5)  # 3 blocks wide

    # 4. 1×2 block
    buildPlatform(0, 20, 20, 8, 9)

    # 5. 2×1 block
    buildPlatform(0, 22, 23, 11, 11)

    # 6. 2×2 block
    buildPlatform(0, 2, 3, 20, 21)

    # 7. Two column (1×3+1×3, stacked separately)
    buildPlatform(0, 6, 7, 12, 14)

    # 8. Two row (3×1+3×1, next to each other)
    buildPlatform(0, 12, 14, 18, 19)

    # 9. Bigger (e.g., 4×4)
    buildPlatform(0, 25, 28, 3, 6)

def buildLevels():
    level = 0

    # 1. Base ground
    buildPlatform(level, 0, 29, 29, 29)

    # 2. First small jump (training)
    buildPlatform(level, 3, 4, 25, 25)

    # 3. Small spring-assisted jump
    buildPlatform(level, 7, 8, 22, 22)
    placeSpringPad(level, 4, 24)

    # 4. Mid-level diamond reward
    buildPlatform(level, 11, 13, 19, 19)
    placeDiamond(level, 12, 18)

    # 5. Key location (risky)
    buildPlatform(level, 16, 16, 22, 23)
    placeKey(level, 16, 21)

    # 6. Spikes as hazard under platform
    placeSpike(level, 16, 28)
    placeSpike(level, 17, 28)
    placeSpike(level, 18, 28)

    # 7. Locked door on upper right
    buildPlatform(level, 22, 24, 17, 17)
    placeLockedDoor(level, 23, 16)

    # 8. Final jump to goal
    buildPlatform(level, 26, 28, 12, 12)
    placeEndFlag(level, 27, 28)

def buildPlatform(level, x1, x2, y1, y2):
    if (y1 == y2) and (x1 == x2):
        # SINGLE BLOCK PLATFORM
        buildBlock(level, y1, x1, 0)

    elif (y1 == y2):
        # ROW PLATFORM
        if (x2 - x1 == 1):
            # 2 BLOCK ROW PLATFORM
            buildBlock(level, y1, x1, 1)
            buildBlock(level, y1, x2, 3)

        else:
            # >2 BLOCK ROW PLATFORM
            buildBlock(level, y1, x1, 1)
            
            for x in range(x1 + 1, x2):
                buildBlock(level, y1, x, 2)

            buildBlock(level, y1, x2, 3)

    elif (x1 == x2):
        # COLUMN PLATFORM
        if (y2 - y1 == 1):
            # 2 BLOCK COLUMN PLATFORM
            buildBlock(level, y1, x1, 20)
            buildBlock(level, y2, x1, 140)

        else:
            # >2 BLOCK COLUMN PLATFORM
            buildBlock(level, y1, x1, 20)
            
            for y in range(y1 + 1, y2):
                buildBlock(level, y, x1, 120)

            buildBlock(level, y2, x1, 140)

    else:
        # 2x2 PLATFORM OR LARGER
        if (x2 - x1 == 1) and (y2 - y1) == 1:
            # 2x2 PLATFORM
            buildBlock(level, y1, x1, 21)
            buildBlock(level, y2, x1, 141)
            buildBlock(level, y1, x2, 23)
            buildBlock(level, y2, x2, 143)
        
        elif (x2 - x1 == 1):
            # 2 COLUMN, >2 ROW PLATFORM
            buildBlock(level, y1, x1, 21)
            buildBlock(level, y1, x2, 23)

            for y in range(y1 + 1, y2):
                buildBlock(level, y, x1, 121)
                buildBlock(level, y, x2, 123)

            buildBlock(level, y2, x1, 141)
            buildBlock(level, y2, x2, 143)

        elif (y2 - y1 == 1):
            # 2 ROW, >2 COLUMN PLATFORM
            buildBlock(level, y1, x1, 21)
            buildBlock(level, y2, x1, 141)

            for x in range(x1 + 1, x2):
                buildBlock(level, y1, x, 22)
                buildBlock(level, y2, x, 142)

            buildBlock(level, y1, x2, 23)
            buildBlock(level, y2, x2, 143)

        else:
            # >2 ROW, >2 COLUMN PLATFORM
            buildBlock(level, y1, x1, 21)
            buildBlock(level, y1, x2, 23)

            for y in range(y1 + 1, y2):
                buildBlock(level, y, x1, 121)
                buildBlock(level, y, x2, 123)

            for x in range(x1 + 1, x2):
                buildBlock(level, y1, x, 22)
                buildBlock(level, y2, x, 142)

            buildBlock(level, y2, x1, 141)
            buildBlock(level, y2, x2, 143)

            for y in range(y1 + 1, y2):
                for x in range(x1 + 1, x2):
                    buildBlock(level, y, x, 122)

def buildBoxPlatform(level, x1, x2, y1, y2):
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            buildBlock(level, y, x, 26)

def placeTree(level, rootsX, rootsY):
    pass

def placeSpringPad(level, x, y):
    buildBlock(level, y, x, 108)
    # add animation using 107

def placeArrowSign(level, x, y, dir):
    if dir == 'right':
        buildBlock(level, y, x, 88)

    else:
        buildBlock(level, y, x, 87)

def placeSignDecoration(level, x, y):
    buildBlock(level, y, x, 85)

def placeKey(level, x, y):
    buildBlock(level, y, x, 27)

def placeLockedDoor(level, x, y):
    buildBlock(level, y, x, 28)

def placeDiamond(level, x, y):
    buildBlock(level, y, x, 67)

def placeSpike(level, x, y):
    buildBlock(level, y, x, 68)

def placeEndFlag(level, x, y):
    global end

    end[level] = [y, x]

def buildBlock(level, y, x, block):
    global data

    data[level][y][x] = block

buildLevels()

players = [Player(4, 0, 'red', 0)]
players_x = [[4, 10, 15, 20, 25], [], [], []]
players_y = [[0, 0, 0, 0, 0], [], [], []]
players_color = [['red', 'blue', 'beige', 'green', 'orange'], [], [], []]

frame = 0

flagFramesPerAnimation = 30
bgFramesPerAnimation = 300

gravity = 0.07
playerJumpPower = 0.75

clock = pygame.time.Clock()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if screenName.startswith('LEVEL'):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    for player in players:
                        if player.ptype == 0:
                            if player.on_ground:
                                player.jump(playerJumpPower)

    screen.fill((0, 0, 0))

    if screenName == 'HOME':
        button_width, button_height = 120, 120
        button_spacing_x = 30
        button_spacing_y = 30
        button_radius = 24
        button_colors = [(70, 130, 180), (60, 179, 113), (218, 165, 32), (205, 92, 92)]
        button_texts = ["1", "2", "3", "4"]
        font = pygame.font.SysFont(None, 70)

        buttons = []
        total_width = 2 * button_width + button_spacing_x
        total_height = 2 * button_height + button_spacing_y
        start_x = (WIDTH - total_width) // 2
        start_y = (HEIGHT - total_height) // 2

        for i in range(2):
            for j in range(2):
                idx = i * 2 + j
                x = start_x + j * (button_width + button_spacing_x)
                y = start_y + i * (button_height + button_spacing_y)
                rect = pygame.Rect(x, y, button_width, button_height)
                buttons.append((rect, button_texts[idx], button_colors[idx]))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for rect, text, color in buttons:
            is_hovered = rect.collidepoint(mouse_pos)
            draw_color = tuple(min(255, c + 30) if is_hovered else c for c in color)
            pygame.draw.rect(screen, draw_color, rect, border_radius=button_radius)
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)
            if is_hovered and mouse_pressed:
                screenName = 'LEVEL' + text

    elif screenName.startswith('LEVEL'):
        bg_frame = round(25*math.sin((frame/bgFramesPerAnimation) - math.pi/2))
        screen.fill((99 - bg_frame, 194 - bg_frame, 205 - bg_frame))

        levelIndex = int(screenName.strip('LEVEL')) - 1
        
        endCoords = end[levelIndex]
        buildBlock(levelIndex, endCoords[0], endCoords[1], 111 if round((frame % flagFramesPerAnimation) / flagFramesPerAnimation) == 0 else 112)

        levelData = data[levelIndex]

        rowIndex = 0
        for row in levelData:
            columnIndex = 0

            for block in row:
                if block != 999:
                    img_path = f'Assets/Tiles/tile_{block:04d}.png'
                    try:
                        img = pygame.image.load(img_path).convert_alpha()
                        img = pygame.transform.scale(img, (18, 18))
                        screen.blit(img, (columnIndex * 18, rowIndex * 18))
                    except pygame.error:
                        pass
                columnIndex += 1
            rowIndex += 1

        for player in players:
            if player.ptype == 0:
                keys = pygame.key.get_pressed()
                player.update(keys[pygame.K_RIGHT] or keys[pygame.K_LEFT], -1 if keys[pygame.K_LEFT] else 1, levelIndex)

            else:
                player.update_existing(levelIndex)

            player.render(screen)

        for i in players:
            for j in players:
                if i != j and not i.finished and not j.finished:
                    if rectangles_overlap(i.x, i.y, j.x, j.y):
                        i.frame_counter = 0

                        if i.ptype == 1:
                            i.update_existing(levelIndex)
                            i.lives -= 0.5

                        else:
                            i.frame_tracker = []
                            i.reset()

                        j.frame_counter = 0

                        if j.ptype == 1:
                            j.update_existing(levelIndex)
                            j.lives -= 0.5

                        else:
                            j.frame_tracker = []
                            j.reset()

                        if i.lives <= 0 or j.lives <= 0:
                            screenName = 'PLAYER_DIED'

        if check_finished() and len(players) < 5:
            ghosts = [player.get_copy_of_self() for player in players]
            idx = len(players)
            players = ghosts
            players.append(Player(players_x[levelIndex][idx], players_y[levelIndex][idx], players_color[levelIndex][idx], 0, []))

        elif check_finished():
            screenName = 'HOME'

    pygame.display.flip()
    clock.tick(60)
    frame += 1

pygame.quit()
sys.exit()