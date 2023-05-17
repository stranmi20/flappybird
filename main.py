# importy
import pygame
import neat
import os
import random
import time
# font
pygame.font.init()

# Rezolution (promenny psane capsem jsou konstantni)
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = -1

# obrazky
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# font
STAT_FONT = pygame.font.SysFont("Roboto", 50)

# Ptak
class Bird:
    # vlastnosti
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    
    # konstruktor
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    # metoda pro skok 
    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y
    
    # metoda pro padani (gravitace)
    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2
        
        if d >= 16:
            d = 16
            
        if d < 0:
            d -= 2
            
        self.y = self.y + d
        
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, win):
        self.img_count += 1
        
        # Animace Ptaka
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2
        
        # rotace obrazku    
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
    
    # metoda pro ziskani masky    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

# Pipe 
class Pipe:
    # vlastnosti
    GAP = 200
    VEL = 5
    
    # konstruktor
    def __init__(self, x):
        self.x = x
        self.height = 0
                
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        
        self.passed = False
        self.set_height()
    
    # metoda pro nastaveni velikosti PIPE_TOP a zmenseni PIPE_BOTTOM (aby byla vyska nahodna)    
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    # metoda pro pohyb
    def move(self):
        self.x -= self.VEL
    
    # metoda pro vkresleni do okna    
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    # metoda pro kolizi s ptakem
    def collide(self, bird):
        # ziskavani masek objektu
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        
        # zjisteni offsetu obou pipe pro overlap
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        
        # zjisteni kolize (vraci true|false)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        
        if t_point or b_point:
            return True
        
        return False

# ground
class Base:
    # vlastnosti
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    
    # konstruktor
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
    
    # metoda pro pohyb (spawnou se dva groundy hnedka za sebou a postupne, az ground bude pryc z okna da se zas za ten druhej)
    def move(self):
        # posouvani
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        # az zmizi da se zpatky za druhej
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        # az zmizi da se zpatky za prvni
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH
    
    # metoda pro vkresleni        
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))     

# funkce pro vykresleni okna
def draw_window(win, birds, pipes, base, score, gen):
    # vkresleni backgroundu
    win.blit(BG_IMG, (0,0))
    
    # vkresleni pipe
    for pipe in pipes:
        pipe.draw(win)
    
    # vkresleni score
    text_score = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text_score, (WIN_WIDTH - 10 - text_score.get_width(), 10))
    
    # vkresleni generace
    text_generation = STAT_FONT.render("Gen: " + str(gen), 1, (255,255,255))
    win.blit(text_generation, (10, 10))
    
    # vkresleni groundu
    base.draw(win)
    
    # ptacci :]]]]
    for bird in birds:
        bird.draw(win)
    
    pygame.display.update()    


# hlavni funkce 
def main(genomes, config):
    # promenne
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []
    
    # pro kazdy g v genech (_,g) - je to tuple (1, g) - potrebujem jen g
    for _, g in genomes:
        # vytvoreni net
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        
        # pridani ptaka do listu - pro kazdy gen jeden ptak
        birds.append(Bird(230,250))
        
        # fitness je 0 a pridam ho do listu
        g.fitness = 0
        ge.append(g)
    
    # zalozeni objektu
    base = Base(730)
    pipes = [Pipe(700)]
    
    # zalozeni okna
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    
    # tick time
    clock = pygame.time.Clock()
    
    score = 0
    run = True
    
    # herni loop
    while run:
        # ticky
        clock.tick(30)
        # vypnuti okna
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            
        # pipe index
        pipe_ind = 0
        
        # pokud pocet ptaku je vic nez nula
        if len(birds) > 0:
            
            # pokud pocet pipe je vic nez 1 AND birdova x souradnice je dal nez pipe (pipe se nachazi za ptakem)
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        
        # pokud ptaku je 0: break
        else:
            run = False
            break
        
        # pro pocet ptaku, ptaku v listu birds        
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            
            # vraci hodntotu mezi -1 a 1 (vyska ptaka, absolutni hodnota(vyska ptaka - vyska pipe[pipe_index]), absolutni hodnota(ptaka vyska - vrsek spodni pipe[pipe_index]))
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            
            # kdyz je 0.5
            if output[0] > -0.99:
                bird.jump()
        
        add_pipe = False
        # list pro remove
        rem = []
        
        # kazda pipe
        for pipe in pipes:
            # pocet ptaku v listu, ptaci
            for x, bird in enumerate(birds):
                # pokud maji kolizi s pipe 
                if pipe.collide(bird):
                    # odstraneni ptaka
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)   
                
                # pokud pipe.paseed = False a ptak je za pipe
                if not pipe.passed and pipe.x < bird.x:
                    # nastavit pipe.passed na true a prida se pipe
                    pipe.passed = True
                    add_pipe = True 
            
            # pokud je pipe offscreen tak se smaze
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            # pipe se pohne
            pipe.move()
        
        # pokud add_pipe = True
        if add_pipe:
            # score se zvedno o 1
            score += 1
            
            # prida se fitness
            for g in ge:
                g.fitness += 5\
            
            # zalozi se nova pipe
            pipes.append(Pipe(600))
        
        # odstraneni pipe   
        for r in rem:
            pipes.remove(r)
        
        # pokud ptak narazi do zeme nebo vyleti ze screenu 
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
         
        # pohyb groundu  
        base.move()
        
        # vykresleni okna
        draw_window(win, birds, pipes, base, score, GEN)
        

# funkce run
def run(config_path):
    # absorbovani configu
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    # nastaveni populace z configu
    p = neat.Population(config)
    
    # hlaseni do konzole true
    p.add_reporter(neat.StdOutReporter(True))
    
    # pridani statu do hlaseni do konzole
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # ptak co dojde nejdal je winner
    winner = p.run(main, 50)


if __name__ == "__main__":
    # zjisteni cesty k configu
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)