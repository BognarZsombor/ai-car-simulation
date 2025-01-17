# This Code is Heavily Inspired By The YouTuber: Cheesy AI
# Code Changed, Optimized And Commented By: NeuralNine (Florian Dedov)

import math
import sys

import neat
import pickle
import pygame

pygame.init()

# Constants
# WIDTH = 1600
# HEIGHT = 880

WIDTH = 1920
HEIGHT = 1080

CAR_SIZE_X = 60
CAR_SIZE_Y = 60

MAP = "map3"
SAVE = "from_map3"

BORDER_COLOR = (255, 255, 255, 255)  # Color To Crash on Hit

current_generation = 0  # Generation counter


class Car:

    def __init__(self, name=""):
        # Load Car Sprite and Rotate
        self.sprite = pygame.image.load('car.png').convert()  # Convert Speeds Up A Lot
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite

        # self.position = [690, 740] # Starting Position
        self.position = [830, 920]  # Starting Position
        self.angle = 0
        self.speed = 0

        self.speed_set = False  # Flag For Default Speed Later on

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2]  # Calculate Center

        self.radars = []  # List For Sensors / Radars
        self.drawing_radars = []  # Radars To Be Drawn

        self.alive = True  # Boolean To Check If Car is Crashed

        self.distance = 0  # Distance Driven
        self.time = 0  # Time Passed
        self.name = name

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "No name given"

    def draw(self, screen, sensor = False):
        screen.blit(self.rotated_sprite, self.position)  # Draw Sprite
        if sensor:
            self.draw_radar(screen)  # OPTIONAL FOR SENSORS

    def draw_radar(self, screen):
        # Optionally Draw All Sensors / Radars
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # If Any Corner Touches Border Color -> Crash
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max) -> go further and further
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])

    def update(self, game_map):
        # Set The Speed To 20 For The First Time
        # Only When Having 4 Output Nodes With Speed Up and Down
        if not self.speed_set:
            self.speed = 5
            self.speed_set = True

        # Get Rotated Sprite And Move Into The Right X-Direction
        # Don't Let The Car Go Closer Than 20px To The Edge
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Increase Distance and Time
        self.distance += self.speed
        self.time += 1

        # Same For Y-Position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # Calculate New Center
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calculate Four Corners
        # Length Is Half The Side
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length,
                    self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length,
                     self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length,
                       self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length,
                        self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check Collisions And Clear Radars
        self.check_collision(game_map)
        self.radars.clear()

        # From -90 To 120 With Step-Size 45 Check Radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Get Distances To Border
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        # Basic Alive Function
        return self.alive

    def get_reward(self):
        return self.distance / (CAR_SIZE_X / 2) / self.time

    def rotate_center(self, image, angle):
        # Rotate The Rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


# if player is None human plays it
# a series of AIs play it on the same map
def play(player=None):
    if player is None:
        # Human player

        # Initialize The Display
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        fps = 60

        # Clock Settings
        # Font Settings & Loading Map
        clock = pygame.time.Clock()
        game_map = pygame.image.load(f'./maps/{MAP}.png').convert()  # Convert Speeds Up A Lot

        car = Car()

        run = True
        while run:
            # Exit On Quit Event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        car.angle += 10  # Left
                    elif event.key == pygame.K_RIGHT:
                        car.angle -= 10  # Right
                    elif event.key == pygame.K_UP:
                        car.speed += 2  # Speed Up
                    elif event.key == pygame.K_DOWN:
                        if car.speed - 2 >= 12:
                            car.speed -= 2  # Slow Down

            screen.blit(game_map, (0, 0))

            if car.is_alive():
                car.update(game_map)
                car.draw(screen)
            else:
                car = Car()

            pygame.display.flip()
            clock.tick(fps)  # 60 FPS
        
        pygame.quit()
        sys.exit()
    else:
        # AI players

        # Initialize The Display
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        fps = 60

        config_path = "./config.txt"
        config = neat.config.Config(neat.DefaultGenome,
                                    neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation,
                                    config_path)
        cars = []
        nets = []
        rewards = []

        for w in player:
            g = pickle.load(open(f"./models/{w}", 'rb'))
            net = neat.nn.FeedForwardNetwork.create(g, config)
            nets.append(net)
            
            cars.append(Car(w.split('.')[0]))
            rewards.append(0)

        # Clock Settings
        # Font Settings & Loading Map
        clock = pygame.time.Clock()
        game_map = pygame.image.load(f'./maps/{MAP}.png').convert()  # Convert Speeds Up A Lot

        run = True
        while run:
            # Exit On Quit Event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break

            for i, car in enumerate(cars):
                output = nets[i].activate(car.get_data())
                choice = output.index(max(output))
                if choice == 0:
                    car.angle += 10  # Left
                elif choice == 1:
                    car.angle -= 10  # Right
                elif choice == 2:
                    if car.speed - 2 >= 12:
                        car.speed -= 2  # Slow Down
                else:
                    car.speed += 2  # Speed Up

            screen.blit(game_map, (0, 0))

            still_alive = 0
            for i, car in enumerate(cars):
                if car.is_alive():
                    still_alive += 1
                    car.update(game_map)
                    car.draw(screen)
                    rewards[i] += car.get_reward()

            if still_alive == 0:
                run = False

            alive_font = pygame.font.SysFont("Arial", 20)
            text = alive_font.render("Still Alive: " + str(still_alive), True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (900, 490)
            screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(fps)  # 60 FPS

        # show leaderboard
        leaderboard = []
        for i, car in enumerate(cars):
            leaderboard.append([car, rewards[i]])
            
        for i, r in enumerate(sorted(leaderboard, key=lambda x: x[1], reverse=True)):
            print(f"{i+1}. {r[0]} Score: {int(r[1])}m")

        # exit
        pygame.quit()
        sys.exit()


def run_simulation(genomes, config):
    # Empty Collections For Nets and Cars
    nets = []
    cars = []

    # Initialize The Display
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    # For All Genomes Passed Create A New Neural Network
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    # Clock Settings
    # Font Settings & Loading Map
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    alive_font = pygame.font.SysFont("Arial", 20)
    game_map = pygame.image.load(f'./maps/{MAP}.png').convert()  # Convert Speeds Up A Lot

    global current_generation
    current_generation += 1

    # Simple Counter To Roughly Limit Time (Not Good Practice)
    counter = 0
    fps = 60

    while True:
        # Exit On Quit Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        # For Each Car Get The Acton It Takes
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10  # Left
            elif choice == 1:
                car.angle -= 10  # Right
            elif choice == 2:
                if car.speed - 2 >= 12:
                    car.speed -= 2  # Slow Down
            else:
                car.speed += 2  # Speed Up

        # Check If Car Is Still Alive
        # Increase Fitness If Yes And Break Loop If Not
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        if still_alive == 0:
            break

        counter += 1
        if counter == fps * 20:  # Stop After About 20 Seconds
            break

        # Draw Map And All Cars That Are Alive
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)

        # Display Info
        text = generation_font.render("Generation: " + str(current_generation), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (900, 450)
        screen.blit(text, text_rect)

        text = alive_font.render("Still Alive: " + str(still_alive), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (900, 490)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(fps)  # 60 FPS


if __name__ == "__main__":
    # play(f'./models/{SAVE}.pkl')
    play(["Bence.pkl", "Zsombor.pkl", "Anna.pkl"])

    # Load Config
    max_gen = 200
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population
    population = neat.Population(config)

    # Load From Checkpoint
    # population = neat.Checkpointer.restore_checkpoint("neat-checkpoint-199")

    # Add Reporters
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    population.add_reporter(neat.Checkpointer(max_gen, None))

    # Run Simulation For A Maximum of 1000 Generations
    winner = population.run(run_simulation, max_gen)

    # Save Winner
    pickle.dump(winner, open(f'./models/{SAVE}.pkl', 'wb'))
