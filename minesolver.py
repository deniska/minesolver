import subprocess
import random
import sys
import re

import pyautogui

pyautogui.PAUSE = 0.01

colors = {
    (192, 192, 192): None,
    (255, 255, 255): None,
    (142, 142, 142): 0,
    (128, 128, 128): 0,
    (  0,   0, 255): 1,
    (  0, 128,   0): 2,
    (255,   0,   0): 3,
    (  0,   0, 128): 4,
    (128,   0,   0): 5,
    (  0, 128, 128): 6,
    # TODO: 7, 8
    (  0,   0,   0): 'game over',
    (170,   0,   0): 'game over',
}

def main():
    region = find_window_using_xwininfo()
    if not region:
        print('Could not find minesweeper window')
        return 1
    tile_size = 24

    left = region[0]
    top = region[1]
    width = (region[2] - region[0]) // tile_size
    height = (region[3] - region[1]) // tile_size

    field = Field(width, height)

    prev_safe_spots = set()
    prev_mines = set()
    while True:
        img = pyautogui.screenshot().crop(region)
        empty = 0
        for y in range(height):
            for x in range(width):
                if (x, y) in prev_mines:
                    continue
                px = tile_size // 2 + tile_size * x
                py = tile_size // 2 + tile_size * y
                color = img.getpixel((px, py))
                res = colors[color]
                if res == 'game over':
                    print('I lost')
                    return 0
                elif res == None:
                    color = img.getpixel((px - tile_size // 2 + 1, py - tile_size // 2 + 1))
                    res = colors[color]
                if res == None:
                    empty += 1
                field[x, y] = colors[color]
        if empty == 0:
            print('I won')
            return 0
        mines, safe_spots = field.solve()
        for x, y in mines - prev_mines:
            mx = left + tile_size // 2 + tile_size * x
            my = top + tile_size // 2 + tile_size * y
            pyautogui.click((mx, my), button='right')
        if safe_spots:
            x, y = random.choice(list(safe_spots))
        else:
            x, y = field.random_spot(mines)
        prev_safe_spots = safe_spots
        prev_mines |= mines
        mx = left + tile_size // 2 + tile_size * x
        my = top + tile_size // 2 + tile_size * y
        pyautogui.click((mx, my))


class Field:
    def __init__(self, width, height):
        self.tiles = [None] * (width * height)
        self.width = width
        self.height = height

    def __getitem__(self, c):
        x, y = c
        return self.tiles[x + y*self.width]

    def __setitem__(self, c, v):
        x, y = c
        self.tiles[x + y*self.width] = v

    def solve(self):
        mines = set()
        for y in range(self.height):
            for x in range(self.width):
                if self[x, y] == 0:
                    continue
                if self[x, y] != None:
                    # count None's around, if equal to self[x, y], then all Nones around are mines
                    none_cnt = 0
                    potential_mines = set()
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                continue
                            if x + dx < 0 or x + dx >= self.width or y + dy < 0 or y + dy >= self.height:
                                continue
                            if self[x + dx, y + dy] == None:
                                potential_mines.add((x + dx, y + dy))
                                none_cnt += 1
                    if none_cnt == self[x, y]:
                        mines |= potential_mines
        # find safe spots
        safe_spots = set()
        for y in range(self.height):
            for x in range(self.width):
                if self[x, y] == 0:
                    continue
                if self[x, y] != None:
                    # count mines around, if equal to self[x, y], then all Nones around are safe spots
                    mine_cnt = 0
                    potential_safe_spots = set()
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                continue
                            if x + dx < 0 or x + dx >= self.width or y + dy < 0 or y + dy >= self.height:
                                continue
                            spot = (x + dx, y + dy)
                            if spot in mines:
                                mine_cnt += 1
                            elif self[spot] == None:
                                potential_safe_spots.add(spot)
                        if mine_cnt == self[x, y]:
                            safe_spots |= potential_safe_spots
        return mines, safe_spots

    def random_spot(self, mines):
        spots = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in mines:
                    continue
                if self[x, y] == None:
                    spots.append((x, y))
        return random.choice(spots)


def find_window_by_images():
    try:
        top_left = pyautogui.locateOnScreen('topleft.png')
        bottom_right = pyautogui.locateOnScreen('bottomright.png')
    except pyautogui.ImageNotFoundException:
        return None

    region = (
        top_left.left + 13,
        top_left.top + 11,
        bottom_right.left + 11,
        bottom_right.top + 10,
    )

    return region


def find_window_using_xwininfo():
    r = subprocess.run(['xwininfo', '-name', 'Minesweeper', '-tree'],
                        stdout=subprocess.PIPE, encoding='utf-8', check=True)
    for line in r.stdout.splitlines():
        if m := re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)  \+(\d+)\+(\d+)', line):
            client_width = int(m[1])
            client_height = int(m[2])
            client_left = int(m[5])
            client_top = int(m[6])
            break
    else:
        return None

    region = (
        client_left + 18,
        client_top + 112,
        client_left + client_width - 12,
        client_top + client_height - 12,
    )

    return region


if __name__ == '__main__':
    sys.exit(main())
