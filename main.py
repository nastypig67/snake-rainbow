import asyncio
import json
import pygame
import random
import pathlib
import sys


pygame.init()

# Running in a web browser (pygbag) or on a computer?
WEB = sys.platform == "emscripten"
PATH = pathlib.Path('top_score.txt')
STORAGE_KEY = 'snake_rainbow_top_score'


def load_top_score():
    # The browser can't keep files, so on the web the score lives in localStorage.
    try:
        if WEB:
            import platform
            value = platform.window.localStorage.getItem(STORAGE_KEY)
            return int(value) if value else 0
        return int(PATH.read_text())
    except Exception:
        return 0


def save_top_score(score):
    try:
        if WEB:
            import platform
            platform.window.localStorage.setItem(STORAGE_KEY, str(score))
        else:
            PATH.write_text(str(score))
    except Exception:
        pass


# ---- Worldwide top 10 (Supabase) ----
# Paste your project's URL and publishable/anon key here (Supabase -> Project Settings -> API Keys).
# The publishable/anon key is safe to share; never put the secret/service_role key here.
SUPABASE_URL = "https://xytdcaocliqyyxblwjpt.supabase.co"
SUPABASE_KEY = "sb_publishable_QXOQdKpab_PUmI4_NtN7PQ_n8-QX9W8"
LEADERBOARD = WEB and SUPABASE_URL != "" and SUPABASE_KEY != ""
NICK_KEY = 'snake_rainbow_nickname'
NICK_MAX = 12

# The browser does the network calls; Python just reads the results each frame,
# so the game never freezes while waiting for the internet.
LEADERBOARD_JS = """
(function (url, key) {
  var headers = { apikey: key, 'Content-Type': 'application/json' };
  if (key.indexOf('eyJ') === 0) headers.Authorization = 'Bearer ' + key;
  window.snakeTop = '[]';
  window.snakeTopStatus = 'loading';
  window.snakeLoadTop = function () {
    window.snakeTopStatus = 'loading';
    fetch(url + '/rest/v1/scores?select=nickname,score&order=score.desc,created_at.asc&limit=10', { headers: headers })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (rows) { window.snakeTop = JSON.stringify(rows); window.snakeTopStatus = 'ok'; })
      .catch(function (e) { console.log('leaderboard load failed', e); window.snakeTopStatus = 'error'; });
  };
  window.snakeSubmit = function (name, score) {
    window.snakeTopStatus = 'loading';
    fetch(url + '/rest/v1/scores', {
      method: 'POST',
      headers: Object.assign({ Prefer: 'return=minimal' }, headers),
      body: JSON.stringify({ nickname: name, score: score })
    })
      .then(function (r) { if (!r.ok) console.log('score submit failed: HTTP ' + r.status); })
      .catch(function (e) { console.log('score submit failed', e); })
      .finally(function () { window.snakeLoadTop(); });
  };
  window.snakeLoadTop();
})(%s, %s);
"""


def js(code):
    try:
        import platform
        return platform.window.eval(code)
    except Exception as e:
        print("leaderboard error:", e)
        return None


def leaderboard_start():
    if LEADERBOARD:
        js(LEADERBOARD_JS % (json.dumps(SUPABASE_URL.rstrip('/')), json.dumps(SUPABASE_KEY)))


def leaderboard_refresh():
    if LEADERBOARD:
        js("window.snakeLoadTop && window.snakeLoadTop()")


def leaderboard_submit(name, score):
    if LEADERBOARD:
        js("window.snakeSubmit(%s, %d)" % (json.dumps(name), int(score)))


def leaderboard_get():
    # returns (status, rows) where status is 'loading', 'ok' or 'error'
    try:
        import platform
        status = str(platform.window.snakeTopStatus)
        rows = json.loads(str(platform.window.snakeTop))
        return status, rows
    except Exception:
        return 'error', []


def load_nickname():
    try:
        import platform
        value = platform.window.localStorage.getItem(NICK_KEY)
        return str(value)[:NICK_MAX] if value else ""
    except Exception:
        return ""


def save_nickname(name):
    try:
        import platform
        platform.window.localStorage.setItem(NICK_KEY, name)
    except Exception:
        pass


COL = 50
ROW = 25
CELL = 20
WIDTH = COL*CELL
HEIGHT = ROW*CELL
screen = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()

RAINBOW = ['red','orange','yellow','green','blue','purple']


def draw_block(pos):
    pygame.draw.rect(screen,'grey',pygame.Rect(pos[0]*CELL,pos[1]*CELL,CELL,CELL))
    pygame.draw.rect(screen,'black',pygame.Rect(pos[0]*CELL,pos[1]*CELL,CELL,CELL),2)


def new_block_spot(snake, blocks, taken):
    while True:
        spot = (random.randint(0,COL-1), random.randint(0,ROW-1))
        if spot not in snake and spot not in blocks and spot not in taken:
            return spot


def draw_apple(pos, color):
    pygame.draw.rect(screen,color,pygame.Rect(pos[0]*CELL,pos[1]*CELL,CELL,CELL))
    pygame.draw.rect(screen,'brown', pygame.Rect((pos[0]+0.5)*CELL,(pos[1]-0.4)*CELL,CELL/10, CELL/2.5))
    pygame.draw.rect(screen,'green', pygame.Rect((pos[0]+0.65)*CELL,(pos[1]-0.25)*CELL, CELL/3, CELL/5))


def draw_rainbow_apple(pos):
    for i in range(6):
        pygame.draw.rect(screen,RAINBOW[i],pygame.Rect(pos[0]*CELL,pos[1]*CELL + i*CELL/6,CELL,CELL/6 + 1))
    pygame.draw.rect(screen,'brown', pygame.Rect((pos[0]+0.5)*CELL,(pos[1]-0.4)*CELL,CELL/10, CELL/2.5))
    pygame.draw.rect(screen,'green', pygame.Rect((pos[0]+0.65)*CELL,(pos[1]-0.25)*CELL, CELL/3, CELL/5))


font1 = pygame.font.SysFont(None,230)
text1 = font1.render('GAME OVER',True,'dark red')
text1_rect = text1.get_rect()
text1_rect.center = screen.get_rect().center

font2 = pygame.font.SysFont(None,40)

text3 = font2.render("Choose a difficulty",True,'black')
text3_rect = text3.get_rect()
text3_rect.top = screen.get_rect().top

font3 = pygame.font.SysFont(None,28)
text4 = font3.render("baby=1, kiddie=2, supereasy=3, easy=4, medium=5, hard=6, superhard=7, insane=8 or impossible=9",True,'black')
text4_rect = text4.get_rect()
text4_rect.center = screen.get_rect().center

text5 = font2.render("Press 'r' to try again",True,'dark red')
text5_rect = text5.get_rect()
text5_rect.bottom = screen.get_rect().bottom

text6 = font2.render("GAME PAUSED",True,'black')
text6_rect = text6.get_rect()
text6_rect.center = screen.get_rect().center

font4 = pygame.font.SysFont(None,25)


def draw_top10(columns, top, font, color):
    # columns: list of (x, y) where each column of names starts; rows are split evenly between them
    status, rows = leaderboard_get()
    x, y = columns[0]
    title = font.render("WORLD TOP 10", True, color)
    screen.blit(title, title.get_rect(midbottom=(WIDTH//2, top)))
    if status == 'loading' and not rows:
        msg = font.render("loading...", True, color)
        screen.blit(msg, (x, y))
        return
    if status == 'error' and not rows:
        msg = font.render("offline - couldn't load the ranking", True, color)
        screen.blit(msg, (x, y))
        return
    if not rows:
        msg = font.render("no scores yet - be the first!", True, color)
        screen.blit(msg, (x, y))
        return
    per_col = (10 + len(columns) - 1) // len(columns)
    line_h = font.get_linesize() + 4
    for i, row in enumerate(rows[:10]):
        cx, cy = columns[i // per_col]
        cy = cy + (i % per_col) * line_h
        name = str(row.get('nickname', '?'))[:NICK_MAX]
        rank = font.render(f"{i+1}.", True, color)
        screen.blit(rank, rank.get_rect(topright=(cx + 30, cy)))
        screen.blit(font.render(name, True, color), (cx + 40, cy))
        score = font.render(str(row.get('score', 0)), True, color)
        screen.blit(score, score.get_rect(topright=(cx + 260, cy)))


async def main():
    top_score = load_top_score()
    leaderboard_start()
    nickname = load_nickname()
    entering_name = False
    name_asked = False
    answer = 1
    sp_x = COL//2
    sp_y = ROW//2
    apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
    snake = []
    gold_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
    green_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
    rainbow_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
    dx = 1
    dy = 0
    snake.append((sp_x,sp_y))

    running = True
    game_over = False
    game_start = False
    game_pause = False
    gold_apple_exist = False
    green_apple_exist = False
    rainbow_apple_exist = False
    points = 0
    time = 0
    time2 = 0
    time3 = 0
    time4 = 0
    time5 = 0
    time6 = 0
    lives = 1
    invincible = False
    invincible_time = 0
    shower_active = False
    shower_time = 0
    shower_accum = 0
    bonus_apples = []
    last_milestone = 0
    milestone_pause = False
    blocks = []
    blocks_exist = False
    time7 = 0
    block_accum = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and entering_name == True:
                # typing a nickname: no other keys do anything until Enter or Esc
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    nickname = nickname.strip()
                    if nickname != "":
                        save_nickname(nickname)
                        leaderboard_submit(nickname, points)
                        entering_name = False
                elif event.key == pygame.K_ESCAPE:
                    entering_name = False
                elif event.key == pygame.K_BACKSPACE:
                    nickname = nickname[:-1]
                elif len(nickname) < NICK_MAX and event.unicode and (event.unicode.isalnum() or event.unicode in " _-."):
                    nickname = nickname + event.unicode
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    dx = 0
                    dy = -1
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    dx = 0
                    dy = 1
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    dx = -1
                    dy = 0
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    dx = 1
                    dy = 0

                if event.key == pygame.K_r:
                    game_over = False
                    game_start = False
                    game_pause = False
                    lives = 1
                    apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
                    snake = []
                    dx = 1
                    dy = 0
                    snake.append((sp_x,sp_y))
                    points = 0
                    time = 0
                    gold_apple_exist = False
                    green_apple_exist = False
                    rainbow_apple_exist = False
                    time6 = 0
                    invincible = False
                    invincible_time = 0
                    shower_active = False
                    shower_time = 0
                    shower_accum = 0
                    bonus_apples = []
                    last_milestone = 0
                    milestone_pause = False
                    time2 = 0
                    time5 = 0
                    blocks = []
                    blocks_exist = False
                    time7 = 0
                    block_accum = 0
                    top_score = load_top_score()
                    name_asked = False
                    entering_name = False
                    leaderboard_refresh()

                if event.key == pygame.K_1:
                    answer = 1
                    game_start = True
                if event.key == pygame.K_2:
                    answer = 3
                    game_start = True
                if event.key == pygame.K_3:
                    answer = 5
                    game_start = True
                if event.key == pygame.K_4:
                    answer = 8
                    game_start = True
                if event.key == pygame.K_5:
                    answer = 10
                    game_start = True
                if event.key == pygame.K_6:
                    answer = 12
                    game_start = True
                if event.key == pygame.K_7:
                    answer = 15
                    game_start = True
                if event.key == pygame. K_8:
                    answer = 22
                    game_start = True
                if event.key == pygame.K_9:
                    answer = 30
                    game_start = True
                if game_start == True and event.key == pygame.K_SPACE:
                    if game_pause == True:
                        game_pause = False
                        milestone_pause = False
                    else:
                        game_pause = True

        # while the rainbow apple's power is running the whole game speeds up by ten
        if invincible == True:
            speed = answer + 10
        else:
            speed = answer

        if game_start == False:
            screen.fill('white')
            screen.blit(text3, text3_rect)
            screen.blit(text4, text4_rect)
            if LEADERBOARD:
                draw_top10([(WIDTH//2 - 330, 340), (WIDTH//2 + 50, 340)], 330, font4, 'black')
        else:
            if game_over == False:
                if game_pause == False:
                    new_head_x = snake[0][0] + dx
                    new_head_y = snake[0][1] + dy
                    if new_head_x == -1 or new_head_y== -1 or new_head_x == COL or new_head_y == ROW or (new_head_x, new_head_y) in snake or (new_head_x, new_head_y) in blocks:
                        if invincible == False:
                            lives = lives - 1
                            print("YOU LOST, FALIURE. GAME OVER!!!!!!!!!!!")
                        if new_head_x == -1: new_head_x = COL-1
                        if new_head_x == COL: new_head_x = 0
                        if new_head_y == -1: new_head_y = ROW-1
                        if new_head_y == ROW: new_head_y = 0
                    if lives == 0:
                        game_over = True
                        continue

                    if points >= last_milestone + 10:
                        last_milestone = (points//10)*10
                        game_pause = True
                        milestone_pause = True

                    snake.insert(0,(new_head_x, new_head_y))
                    ate = False
                    if apple == snake[0]:
                        apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
                        points = points + 1
                        ate = True
                    elif gold_apple == snake[0] and gold_apple_exist == True:
                        points = points + 5
                        gold_apple_exist = False
                        ate = True
                    elif green_apple == snake[0] and green_apple_exist == True:
                        lives = lives + 1
                        green_apple_exist = False
                        ate = True
                    elif rainbow_apple == snake[0] and rainbow_apple_exist == True:
                        rainbow_apple_exist = False
                        invincible = True
                        invincible_time = 0
                        shower_active = True
                        shower_time = 0
                        shower_accum = 0
                        ate = True
                    else:
                        for bonus in bonus_apples:
                            if (bonus[0], bonus[1]) == snake[0]:
                                if bonus[2] == 'red':
                                    points = points + 1
                                elif bonus[2] == 'gold':
                                    points = points + 5
                                else:
                                    lives = lives + 1
                                bonus_apples.remove(bonus)
                                ate = True
                                break
                    if ate == False:
                        snake.pop()

                    if gold_apple_exist == False and random.randint(1, 100)== 1:
                        gold_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
                        gold_apple_exist = True
                        time3 = 0
                    if time3 >= 3:
                        gold_apple_exist = False

                    if green_apple_exist == False and random.randint(1, 300)== 1:
                        green_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
                        green_apple_exist = True
                        time4 = 0

                    if time4 >= 3:
                        green_apple_exist = False

                    if rainbow_apple_exist == False and invincible == False and random.randint(1, 10)== 1:
                        rainbow_apple = (random.randint(0,COL-1), random.randint(0,ROW-1))
                        rainbow_apple_exist = True
                        time6 = 0

                    if time6 >= 5:
                        rainbow_apple_exist = False

                    # five kill blocks appear, then one more every three seconds for twenty seconds
                    if blocks_exist == False and random.randint(1, 200)== 1:
                        blocks = []
                        taken = [apple, gold_apple, green_apple, rainbow_apple, ((snake[0][0]+dx) % COL, (snake[0][1]+dy) % ROW)]
                        for i in range(5):
                            blocks.append(new_block_spot(snake, blocks, taken))
                        blocks_exist = True
                        time7 = 0
                        block_accum = 0

                    if blocks_exist == True:
                        time7 = time7 + 1/speed
                        block_accum = block_accum + 1/speed
                        while block_accum >= 3:
                            block_accum = block_accum - 3
                            taken = [apple, gold_apple, green_apple, rainbow_apple, ((snake[0][0]+dx) % COL, (snake[0][1]+dy) % ROW)]
                            blocks.append(new_block_spot(snake, blocks, taken))
                        if time7 >= 20:
                            blocks_exist = False
                            blocks = []
                            block_accum = 0

                    # the ten seconds of invincibility and extra speed
                    if invincible == True:
                        invincible_time = invincible_time + 1/speed
                        if invincible_time >= 10:
                            invincible = False

                    # twenty seconds of two random apples raining down every second
                    if shower_active == True:
                        shower_time = shower_time + 1/speed
                        shower_accum = shower_accum + 1/speed
                        while shower_accum >= 1:
                            shower_accum = shower_accum - 1
                            for i in range(2):
                                bonus_apples.append((random.randint(0,COL-1), random.randint(0,ROW-1), random.choice(['red','gold','green'])))
                        if shower_time >= 20:
                            shower_active = False
                            bonus_apples = []


                    screen.fill('white')
                    # for i in range(COL):
                    #     pygame.draw.line(screen,'black',(i*CELL,0), (i*CELL,HEIGHT))
                    # for i in range(ROW):
                    #     pygame.draw.line(screen, 'black', (0, i*CELL), (WIDTH, i*CELL))

                    draw_apple(apple, 'red')

                    for bonus in bonus_apples:
                        if bonus[2] == 'red':
                            draw_apple(bonus, 'red')
                        elif bonus[2] == 'gold':
                            draw_apple(bonus, 'gold')
                        else:
                            draw_apple(bonus, 'green')

                    for block in blocks:
                        draw_block(block)

                    if invincible == True:
                        snake_colour = RAINBOW[int(time*10) % 6]
                    else:
                        snake_colour = 'dark green'
                    for i in range(len(snake)):
                        pygame.draw.rect(screen,snake_colour,pygame.Rect(snake[i][0]*CELL,snake[i][1]*CELL,CELL,CELL))
                    score_line = f"points:{points}   lives: {lives}   top score: {top_score}"
                    if invincible == True:
                        score_line = score_line + f"   RAINBOW {10-invincible_time:.1f}s"
                    if shower_active == True:
                        score_line = score_line + f"   SHOWER {20-shower_time:.1f}s"
                    if blocks_exist == True:
                        score_line = score_line + f"   BLOCKS {len(blocks)} / {20-time7:.1f}s"
                    text8 = font3.render(score_line,True,'blue')
                    text8_rect = text8.get_rect()
                    text8_rect.topleft = screen.get_rect().topleft
                    screen.blit(text8, text8_rect)

                    if dx == 0 and dy == -1:
                        pygame.draw.rect(screen,'red',pygame.Rect((snake[0][0]+ 0.5)*CELL,(snake[0][1]-0.5)*CELL,CELL/6,CELL/2))
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.25)*CELL,(snake[0][1]+0.25)*CELL), CELL/10)
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.75)*CELL,(snake[0][1]+0.25)*CELL), CELL/10)
                    if dx == 0 and dy == 1:
                        pygame.draw.rect(screen,'red',pygame.Rect((snake[0][0]+ 0.5)*CELL,(snake[0][1]+1)*CELL,CELL/6,CELL/2))
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.25)*CELL,(snake[0][1]+0.75)*CELL), CELL/10)
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.75)*CELL,(snake[0][1]+0.75)*CELL), CELL/10)
                    if dx == -1 and dy == 0:
                        pygame.draw.rect(screen,'red',pygame.Rect((snake[0][0]-0.5)*CELL,(snake[0][1]+ 0.5)*CELL,CELL/2,CELL/6))
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.25)*CELL,(snake[0][1]+0.25)*CELL), CELL/10)
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.25)*CELL,(snake[0][1]+0.75)*CELL), CELL/10)
                    if dx == 1 and dy == 0:
                        pygame.draw.rect(screen,'red',pygame.Rect((snake[0][0]+1)*CELL,(snake[0][1]+ 0.5)*CELL,CELL/2,CELL/6))
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.75)*CELL,(snake[0][1]+0.25)*CELL), CELL/10)
                        pygame.draw.circle(screen, 'black', ((snake[0][0]+0.75)*CELL,(snake[0][1]+0.75)*CELL), CELL/10)
                    if gold_apple_exist == True:
                        draw_apple(gold_apple, 'gold')
                        time3 = time3 + 1/speed

                    if green_apple_exist == True:
                        draw_apple(green_apple, 'green')
                        time4 = time4 + 1/speed

                    if rainbow_apple_exist == True:
                        draw_rainbow_apple(rainbow_apple)
                        time6 = time6 + 1/speed

                else:

                    if points >= 100:
                        screen.fill('white')
                        text9 = font4.render("Well done! You are officially a snake champion.",True,'black')
                        text9_rect = text9.get_rect()
                        text9_rect.center = screen.get_rect().center
                        screen.blit(text9, text9_rect)
                        time5 = time5 + 1/speed
                    elif milestone_pause == True:
                        screen.fill('white')
                        text7 = font4.render(f"Well done. Keep going. You've already earned {last_milestone} points. I'll give you one more point as a reward. Get ready!",True,'black')
                        text7_rect = text7.get_rect()
                        text7_rect.center = screen.get_rect().center
                        screen.blit(text7, text7_rect)
                        time2 = time2 + 1/speed
                    else:
                        screen.fill('white')
                        screen.blit(text6, text6_rect)


                    if time2 >= 5:
                        points = points + 1
                        game_pause = False
                        milestone_pause = False
                        time2 = 0
                    if time5 >=5 :
                        game_over = True
                        continue


                time = time + 1/speed

            else:
                if name_asked == False:
                    name_asked = True
                    entering_name = LEADERBOARD and points > 0
                text2 = font2.render(f"You earned {points} points in {time:.2f} seconds!",True,'white')
                text2_rect = text2.get_rect()
                screen.fill('black')
                if LEADERBOARD and entering_name == False:
                    # after the name step: show the world ranking
                    text2_rect.midtop = (WIDTH//2, 15)
                    screen.blit(text2,text2_rect)
                    draw_top10([(WIDTH//2 - 150, 110)], 100, font2, 'white')
                    screen.blit(text5, text5_rect)
                else:
                    text2_rect.center = screen.get_rect().center
                    text2_rect.centery = text2_rect.centery + 100
                    screen.blit(text1,text1_rect)
                    screen.blit(text2,text2_rect)
                    if entering_name == True:
                        cursor = "_" if pygame.time.get_ticks() // 400 % 2 == 0 else " "
                        prompt = font3.render(f"Your nickname for the world ranking: {nickname}{cursor}", True, 'yellow')
                        screen.blit(prompt, prompt.get_rect(center=(WIDTH//2, 405)))
                        hint = font4.render("Enter = send     Esc = skip", True, 'grey')
                        screen.blit(hint, hint.get_rect(center=(WIDTH//2, 440)))
                    else:
                        screen.blit(text5, text5_rect)
                if top_score < points:
                    save_top_score(points)
                    top_score = points

        pygame.display.flip()
        # menus and the game-over screen run at 30 fps so typing feels instant
        clock.tick(30 if game_start == False or game_over == True else speed) # baby=1, kiddie=3, super easy=5, easy=8, medium=10, hard=15, super hard=20, insane=25, impossible=30
        await asyncio.sleep(0)  # hands control back to the browser each frame; pygbag needs this

    pygame.quit()


asyncio.run(main())
