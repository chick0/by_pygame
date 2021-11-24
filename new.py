from os import urandom
from sys import exit
from time import time
from random import choice
from random import randint
import pygame
from pygame.locals import *

pygame.init()

font = pygame.font.Font("font/NotoSansKR-Bold.otf", 16)
big_font = pygame.font.Font("font/NotoSansKR-Bold.otf", 63)

clock = pygame.time.Clock()
pygame.display.set_caption("Space Invaders")

screen = pygame.display.set_mode((640, 650))

bad_guy_image = pygame.image.load("images/badguy.png").convert()
bad_guy_image.set_colorkey((0, 0, 0))

fighter_image = pygame.image.load("images/fighter.png").convert()
fighter_image.set_colorkey((255, 255, 255))

missile_image = pygame.image.load("images/missile.png").convert()
missile_image.set_colorkey((255, 255, 255))

life_images = {
    0: pygame.image.load("images/lives_0G.png").convert(),
    1: pygame.image.load("images/lives_1G.png").convert(),
    2: pygame.image.load("images/lives_2G.png").convert(),
    3: pygame.image.load("images/lives_3G.png").convert(),
}

for life_img in life_images.values():
    life_img.set_colorkey((0, 0, 0))


def safe_delete(some_object, key):
    try:
        del some_object[key]
    except KeyError:
        pass


class Score:
    def __init__(self):
        self._start = time()
        self._end = time()
        self._shoot = 0

    def add_shoot_point(self) -> None:
        self._shoot += 1

    def get_shoot_score(self) -> int:
        return self._shoot

    def timer_update(self) -> int:
        self._end = time()
        return round(self._end - self._start)

    @property
    def survive(self) -> int:
        return round(self._end - self._start) * 5

    @property
    def shoot(self) -> int:
        return self._shoot * 30

    @property
    def total(self) -> int:
        return self.survive + self.shoot


class BadGuy:
    def __init__(self, bid_):
        self.id = bid_

        self.x = randint(0, 570)
        self.y = -100
        self.dy = randint(2, 6)
        self.dx = choice((-1, 1)) * self.dy

    def update(self):
        # move
        self.x += self.dx
        self.dy += 0.05
        self.y += self.dy

        # bounce
        if self.x < 0 or self.x > 570:
            self.dx *= -1

        # draw
        screen.blit(bad_guy_image, (self.x, self.y))

        # delete
        if self.y > 640:
            safe_delete(bad_guys, self.id)

    def check_touching(self, missile) -> bool:
        if pygame.Rect((self.x, self.y), (70, 45)).collidepoint(missile.x, missile.y):
            score.add_shoot_point()
            safe_delete(bad_guys, self.id)

            return True
        else:
            return False

    def __repr__(self):
        return f"<BadGuy id={self.id!r}>"


class Fighter:
    def __init__(self):
        self.x = 320
        self.y = 591

        self.last_shoot = time()
        self.hp = 3

        self.gun_temp = 30
        self.shoot_memory = False
        self.gun_last_cool = time()

        self.total_shoot = 0

    def shoot(self):
        def gen_mid() -> str:
            t = urandom(4).hex()
            if t in missiles.keys():
                return gen_mid()

            return t

        if self.gun_temp < 100 and time() - self.last_shoot > 0.14:
            mid = gen_mid()  # mid == Missile ID
            missiles[mid] = Missile(mid, x=self.x + 50)

            self.last_shoot = time()
            self.gun_temp += 2
            self.shoot_memory = True

            self.total_shoot += 1

    def update(self):
        pressed_keys = pygame.key.get_pressed()

        # move
        if pressed_keys[K_LEFT] and self.x > 0:
            self.x -= 3
        if pressed_keys[K_RIGHT] and self.x < 540:
            self.x += 3

        # shoot
        if pressed_keys[K_SPACE]:
            self.shoot()
        else:
            self.shoot_memory = False

        # draw
        screen.blit(fighter_image, (self.x, self.y))

    def touched_with(self, target: BadGuy) -> bool:
        if pygame.Rect((self.x, self.y), (70, 50)).collidepoint(target.x, target.y):
            safe_delete(bad_guys, target.id)
            self.hp -= 1

            return True
        else:
            return False


class Missile:
    def __init__(self, mid, x):
        self.id = mid
        self.x = x
        self.y = 591

    def update(self):
        # move
        self.y -= 5

        # draw
        screen.blit(missile_image, (self.x - 4, self.y))

        # delete
        if self.y < -8:
            safe_delete(missiles, self.id)


score = Score()

bad_guys = {}
last_bad_guy_spawn_time = 0

fighter = Fighter()

missiles = {}

while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()

    screen.fill((0, 0, 0))
    fighter.update()

    if time() - last_bad_guy_spawn_time > 0.19:
        def gen_bid() -> str:
            t = urandom(4).hex()
            if t in bad_guys.keys():
                return gen_bid()

            return t


        bid = gen_bid()  # bid == BadGuy ID
        bad_guys[bid] = BadGuy(bid)

        last_bad_guy_spawn_time = time()

    for bad_guy_id in list(bad_guys.keys()):
        if not fighter.touched_with(bad_guys[bad_guy_id]):
            bad_guys[bad_guy_id].update()

    for missile_id in list(missiles.keys()):
        missiles[missile_id].update()

        for bad_guy_id in list(bad_guys.keys()):
            try:
                if bad_guys[bad_guy_id].check_touching(missiles[missile_id]):
                    safe_delete(missiles, missile_id)
            except KeyError:
                pass

    if fighter.shoot_memory is False and fighter.gun_temp > 30:
        if time() - fighter.gun_last_cool > 0.35:
            fighter.gun_temp -= 1
            fighter.gun_last_cool = time()

    # 내구도 == HP
    hp_text = font.render("내구도", True, (255, 255, 255), (0, 0, 0))
    screen.blit(hp_text, (5, 5))
    screen.blit(
        life_images.get(fighter.hp),
        (13.5, 30)
    )

    # 온도 표시
    # - 의미 전달이 안될것 같아서 표시 명칭변경
    temp_text = font.render("부하율", True, (255, 255, 255), (0, 0, 0))
    screen.blit(temp_text, (60, 5))
    screen.blit(
        font.render(f"{fighter.gun_temp} %", True, (255, 255, 255), (0, 0, 0)),
        (63, 30)
    )

    pygame.display.update()

    if fighter.hp <= 0:
        survive_time = score.timer_update()

        game_over = True
        while game_over:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()

            ge = big_font.render(" 게임종료 ", True, (255, 255, 255), (220, 20, 60))
            xx = (screen.get_width() - ge.get_width()) / 2
            screen.blit(ge, (xx, 100))

            sc_tp = big_font.render(f"{score.total} 점", True, (255, 255, 255), (0, 0, 0))
            screen.blit(sc_tp, ((screen.get_width() - sc_tp.get_width()) / 2, 195))

            s_text = font.render(f"공격 점수 : {score.shoot} 점", True, (255, 255, 255), (0, 0, 0))
            t_text = font.render(f"시간 점수 : {score.survive} 점", True, (255, 255, 255), (0, 0, 0))

            screen.blit(s_text, (xx, 300))
            screen.blit(t_text, (xx, 330))

            press_enter = font.render("[Enter]키를 눌러서 다시 시작", True, (255, 255, 255), (0, 0, 0))
            screen.blit(press_enter, ((screen.get_width() - press_enter.get_width()) / 2, 400))

            _pressed_keys = pygame.key.get_pressed()
            if _pressed_keys[K_RETURN]:
                game_over = False

                # 전역변수를 초기화해서 게임상테 초기화
                globals().update({
                    "score": Score(),
                    "bad_guys": {},
                    "last_bad_guy_spawn_time": 0,
                    "fighter": Fighter(),
                    "missiles": {}
                })

            pygame.display.update()
