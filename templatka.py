# -*- coding: utf-8 -*-

from psychopy import visual, event, core
import multiprocessing as mp
import pygame as pg
import pandas as pd
import filterlib as flt
import blink as blk
#from pyOpenBCI import OpenBCIGanglion


def blinks_detector(quit_program, blink_det, blinks_num, blink,):
    def detect_blinks(sample):
        if SYMULACJA_SYGNALU:
            smp_flted = sample
        else:
            smp = sample.channels_data[0]
            smp_flted = frt.filterIIR(smp, 0)
        #print(smp_flted)

        brt.blink_detect(smp_flted, -38000)
        if brt.new_blink:
            if brt.blinks_num == 1:
                #connected.set()
                print('CONNECTED. Speller starts detecting blinks.')
            else:
                blink_det.put(brt.blinks_num)
                blinks_num.value = brt.blinks_num
                blink.value = 1

        if quit_program.is_set():
            if not SYMULACJA_SYGNALU:
                print('Disconnect signal sent...')
                board.stop_stream()


####################################################
    SYMULACJA_SYGNALU = True
####################################################
    mac_adress = 'd2:b4:11:81:48:ad'
####################################################

    clock = pg.time.Clock()
    frt = flt.FltRealTime()
    brt = blk.BlinkRealTime()

    if SYMULACJA_SYGNALU:
        df = pd.read_csv('dane_do_symulacji/data.csv')
        for sample in df['signal']:
            if quit_program.is_set():
                break
            detect_blinks(sample)
            clock.tick(200)
        print('KONIEC SYGNAŁU')
        quit_program.set()
    else:
        board = OpenBCIGanglion(mac=mac_adress)
        board.start_stream(detect_blinks)

if __name__ == "__main__":


    blink_det = mp.Queue()
    blink = mp.Value('i', 0)
    blinks_num = mp.Value('i', 0)
    #connected = mp.Event()
    quit_program = mp.Event()

    proc_blink_det = mp.Process(
        name='proc_',
        target=blinks_detector,
        args=(quit_program, blink_det, blinks_num, blink,)
        )

    # rozpoczęcie podprocesu
    proc_blink_det.start()
    print('subprocess started')

    ############################################
    # Poniżej należy dodać rozwinięcie programu
    ############################################

    import pygame
    from Camera import Camera
    from Player import Player
    from Platform import Platform
    from Platform_controller import PlatformController
    from pygame.locals import *

    #text
    def text_objects(text, font, color):
        textSurface = font.render(text, True, color)
        return textSurface, textSurface.get_rect()

    def message_display(window, text, x, y, font_size, color, centered_x=False, centered_y=False):
        font = pygame.font.Font(None,font_size)
        TextSurf, TextRect = text_objects(text, font, color)
        if centered_x and centered_y:
        	TextRect.center = ((W/2),(H/2))
        elif centered_x:
        	TextRect.center = ((W/2),y)
        elif centered_y:
        	TextRect.center = (x,(H/2))
        else:
        	TextRect.center = (x,y)
        window.blit(TextSurf, TextRect)

    #colors
    background = (123, 174, 163)
    black = (0,0,0)
    blue = (0,0, 255)
    white = (255,255,255)

    #window
    pygame.init()
    H = 650
    W = 600
    GRAVITY = 1
    JUMP_SPEED = 15
    MAX_JUMP = 150
    window = pygame.display.set_mode((W, H))
    window.fill(background)

    #title and icon
    pygame.display.set_caption("Jump the tower")
    icon = pygame.image.load('duck.png')
    pygame.display.set_icon(icon)

    def reinit():
        global player
        global camera
        global platform_controller
        global floor
        player = Player()
        platform_controller = PlatformController()
        camera = Camera(player)
        floor = Platform(0, H-36, W, 36)

    player = Player()
    platform_controller = PlatformController()
    floor = Platform(0, H-36, W, 36)

    selected_option = 0.30
    camera = Camera(player)
    clock = pygame.time.Clock()
    fps = 60

    def event():
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    game == False
                    pygame.quit()
                # PLAYER JUMPS
        if blink.value==1:
            if player.on_any_platform(platform_controller, floor):
                if player.speed_y >= JUMP_SPEED/2:
                    player.speed_y = -JUMP_SPEED

    def game_over():
        window = pygame.display.set_mode((W, H))
        window.fill(black)
        game_over_img = pygame.image.load('game-over.png')
        window.blit(game_over_img, (W/2 - 64, H/2 - 160))
        message_display(window, "Score: %d" % player.score, 0, 300, 50, white, True)
        message_display(window, "Press SPACE to play again!", 0, 370, 50, white, True)
        message_display(window, "Press ESC to quit!", 0, 440, 40, white, True)
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    game == False
                    pygame.quit()
        if blinks.value==1:
            reinit()

    game = True
    #game loop
    while game:
            event()

            player.update(platform_controller)
            player.collide_platform(floor,0)
            platform_controller.update()
            platform_controller.collide_set(player)
            platform_controller.score = player.score
            camera.update(player.score)
            platform_controller.generate_new_platforms(camera)

            window.fill(background)
            floor.draw(window, camera)
            platform_controller.draw(window, camera)
            player.draw(window, camera)
            message_display(window, str(player.score), 25, 30, 36, white)

            if player.fallen_off_screen(camera) == True:
                game_over()

            pygame.display.update()
            clock.tick(fps)


    win = visual.Window(
        size=[500, 500],
        units="pix",
        fullscr=False
    )

    while True:
        if blink.value == 1:
            print('BLINK!')
            blink.value = 1
        if 'escape' in event.getKeys():
            print('quitting')
            quit_program.set()
        if quit_program.is_set():
            break

# Zakończenie podprocesów
    proc_blink_det.join()
