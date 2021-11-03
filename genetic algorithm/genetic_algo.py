"""
This program demonstrate using genetic algorithm to find a path, short as possible, between two points in a grid.
The starting point is known, while the finish point is unknown.

The starting and finishing point are selected randomly.
We'll use a large pool of possible solutions (we'll call them "chromosomes"),
 and the genetic algorithm will pick the best routs to the finish point

 To run this program successfully you must have numpy and matplotlib installed

The running time of this program is directly depends on how big the greed is,
and on how many obstacle are in the greed.

"""

import random
from tkinter import *
from grid_gui import CellGrid

NUM_CHROMOSOMES = 100  # how many chromosomes will be created  # CAN BE ONLY A MULTIPLICATION OF 10!
NUM_GENERATIONS = 1000  # how many generations the function will run
STOP_CONDITION = 200  # if there's no change in the average fitness value in this amount of generation
# the program will return the results.


# DO NOT CHANGE  ###
N = 40
GRID_SIZE = 700
NUM_CHILDREN = NUM_CHROMOSOMES // 20  # max number of the new chromosome created out of the selected parents
NUM_DEATH = NUM_CHILDREN // 2

# Obstacles
THROW_OBSTACLES = 1  # "on-off switch" weather to put obstacles in the greed or not

# DO NOT CHANGE  ###
START = 11  # represent the start position
FINISH = 12  # represent the finish position
OBSTACLE = 1  # represent an obstacle
EMPTY = 0

# constants to represent a directions of moving in the greed
DEFAULT = 0
UP = 1
DOWN = 2
RIGHT = 3
LEFT = 4

DIRECTIONS = 4  # number of directions

# GUI VALUES
BUTTON_BAR_HEIGHT = 60


# the fitness function ##
# for a chromosome "a" the value of a is depends on its length and how far it is from the finish point.


class Monitor:

    def __init__(self):
        self.s_point = self.e_point = (0, 0)
        self.grid = []
        self.num_obstacles = 0
        self.gui_cells = None
        self.min_length = 0
        self.max_length = 0
        self.founded = False

        self.num_path = 0

    def run_gui(self, app):
        """ Execute the GUI of the program. The program gets the app variable which is an instance
         of the Tkinter """

        my_frame = Frame(app)
        my_frame.pack(fill=X, expand=YES)

        cells_width = cells_height = int(GRID_SIZE / N) * N
        button_bar_width = cells_width
        button_bar_height = BUTTON_BAR_HEIGHT

        self.gui_cells = CellGrid(app, self, N, width=max(cells_width, button_bar_width),
                                  height=button_bar_height + cells_height)
        self.gui_cells.pack(fill=X, expand=YES)

        app.mainloop()

    def run(self, grid, s_point, e_point):
        self.s_point = s_point
        self.e_point = e_point
        self.grid = grid.copy()

        self.gui_cells.change_status("Adding obstacles...")
        for i in grid:
            for j in i:
                if j == OBSTACLE:
                    self.num_obstacles += 1
                else:
                    self.num_path += 1

        # create the initial population
        self.gui_cells.change_status("Initializing population...")
        pool = self.generate_pool()

        # run the genetic algorithm
        self.run_generations(pool)

        # make available to clear
        self.gui_cells.button_clear['state'] = NORMAL

    def clear(self):
        self.s_point = self.e_point = (0, 0)
        self.grid = []
        self.num_obstacles = 0

    def generate_pool(self):
        pool = []
        self.min_length = manhattan_distance(self.s_point, self.e_point)
        self.max_length = self.num_path
        while len(pool) < NUM_CHROMOSOMES:
            chrom = Chromosome(self.s_point, self.e_point)
            chrom.generate(self.min_length, self.max_length, self.grid)
            pool.append(chrom)

        return pool

    def run_generations(self, pool):
        # show the first generation's paths on the grid

        self.gui_cells.change_status("First generation...")
        self.gui_cells.update()
        self.gui_cells.show_generations(pool)

        for i in range(NUM_GENERATIONS):
            self.make_more(pool)
            self.kill_some(pool)
            self.gui_cells.change_status("generation {}".format(i+2))
            # if (i + 2) % 5 == 0:
            self.gui_cells.update()
            self.stats(pool, i + 1)
            print(len(pool))

        self.gui_cells.show_generations(pool)
        self.gui_cells.change_status("Finished")
        self.gui_cells.update()

    def make_more(self, pool):
        for _ in range(NUM_CHILDREN):
            parent1 = roulette_wheel(pool)
            pool.remove(parent1)
            parent2 = roulette_wheel(pool)
            pool.remove(parent2)

            if random.randint(0, 1):
                temp = parent1
                parent1 = parent2
                parent2 = temp

            parent1.parent_value += 1
            parent2.parent_value += 1

            child = self.make_child(parent1, parent2)
            if child.length == 0:
                child = Chromosome(self.s_point, self.e_point)
                child.generate(self.min_length, self.max_length, self.grid)

            self.gui_cells.show_generations([child])
            pool.extend([child, parent1, parent2])

    def make_child(self, parent1, parent2):
        child = Chromosome(self.s_point, self.e_point)

        divider = random.randint(0, min(len(parent1.list_dir), len(parent2.list_dir)))
        part1 = parent1.list_dir[:divider]
        part2 = parent2.list_dir[divider:]

        child.list_dir = part1 + part2
        mutation(child)
        self.adjust_child(child)
        return child

    def adjust_child(self, child):
        dir_list = []
        point_set = set()
        curr_point = self.s_point
        point_set.add(curr_point)
        for direction in child.list_dir:
            if curr_point != self.e_point:
                if is_safe(curr_point, direction, self.grid):
                    dir_list.append(direction)
                    curr_point = move(curr_point, direction)
                    point_set.add(curr_point)
                else:
                    child.length = 0
                    return child

            else:
                break

        child.list_dir = dir_list.copy()
        child.set_points = point_set.copy()
        child.distance = manhattan_distance(curr_point, self.e_point)
        child.cal_fitness()

    def kill_some(self, pool):
        for _ in range(len(pool) - NUM_CHROMOSOMES):
            candidate = reverse_roulette_wheel(pool)
            if candidate.parent_value > 0:
                candidate.parent_value -= 1
            else:
                pool.remove(candidate)
                self.gui_cells.clear_chrom(candidate)

    def stats(self, pool, i):
        pass


def roulette_wheel(pool):
    fit_values = [chrom.fitness_value for chrom in pool]
    max_value = sum(fit_values)
    pick = random.uniform(0, max_value)  # pick a random value between the sum and 0
    current = 0

    #  the bigger values have more chance to get picked
    for chrom in pool:
        current += chrom.fitness_value
        if current > pick:
            return chrom


def reverse_roulette_wheel(pool):
    fit_values = [1/chrom.fitness_value for chrom in pool]
    max_value = sum(fit_values)
    pick = random.uniform(0, max_value)
    current = 0

    for chrom in pool:
        current += 1/chrom.fitness_value
        if current > pick:
            return chrom


def manhattan_distance(start, finish):
    return abs(start[0] - finish[0]) + abs(start[1] - finish[1])


def main():
    monitor = Monitor()
    app = Tk()
    monitor.run_gui(app)


class Chromosome:
    """
    This class defines a chromosome and its properties.
    A chromosome is basically a single solution for our problem and its main property is a path -
    a list of directions from the start point.
    The class provides a function to generate the path, and a function to calculate the fitness value which is
    one of the most important concepts in our program.
    """

    def __init__(self, s_point, e_point):
        self.distance = 0
        self.set_points = set()
        self.list_dir = []
        self.length = 0
        self.fitness_value = 0
        self.parent_value = 0
        self.s_point = s_point
        self.e_point = e_point

        self.stuck = False

    def generate(self, min_length, max_length, grid):
        curr_point = self.s_point

        length = random.randint(min_length, max_length)      # length of the chromosome will be randomize

        while curr_point != self.e_point and len(self.set_points) < length:
            directions = [UP, DOWN, RIGHT, LEFT]
            while directions:
                rand = random.choice(directions)        # randomly choose a direction
                if is_safe(curr_point, rand, grid):     # check if a move in this direction is valid
                    candidate = move(curr_point, rand)

                    old_length = len(self.set_points)
                    self.set_points.add(candidate)
                    if old_length == len(self.s_point):
                        directions.remove(rand)
                        break
                    else:
                        curr_point = candidate
                        self.list_dir.append(rand)

                else:
                    directions.remove(rand)  # choose another direction

            # generate only valid paths
            if not directions:
                self.stuck = True
                break

        # calculate the distance from the end of the path to the finish point
        self.distance = manhattan_distance(curr_point, self.e_point)
        self.cal_fitness()

    def cal_fitness(self):
        self.length = len(self.set_points)
        value = 1/(((self.distance + 1) ** 8) + (self.length ** 3) + ((len(self.list_dir) - len(self.set_points)) ** 4))
        self.fitness_value = value


# *************** end of class Chromosome ****************************
# ********************************************************************

# move in a certain point in a given direction
def move(point, direction):
    point_l = list(point)

    if direction == UP:
        point_l[0] -= 1
    elif direction == DOWN:
        point_l[0] += 1
    elif direction == RIGHT:
        point_l[1] += 1
    elif direction == LEFT:
        point_l[1] -= 1
    return tuple(point_l)


# check if a direction is safe to move to (checking obstacles and boundaries
def is_safe(point, direction, matrix):
    excluded_options = [OBSTACLE, START]

    if direction == DEFAULT:
        if 0 <= point[0] < len(matrix) and 0 <= point[1] < len(matrix[0]) and matrix[point[0]][point[1]] != OBSTACLE:
            return True
    elif direction == UP:
        if point[0] > 0 and matrix[point[0] - 1][point[1]] not in excluded_options:
            return True
    elif direction == DOWN:
        if point[0] < len(matrix) - 1 and matrix[point[0] + 1][point[1]] not in excluded_options:
            return True
    elif direction == RIGHT:
        if point[1] < len(matrix[0]) - 1 and matrix[point[0]][point[1] + 1] not in excluded_options:
            return True
    elif direction == LEFT:
        if point[1] > 0 and matrix[point[0]][point[1] - 1] not in excluded_options:
            return True

    return False


# present a possible mutation to a single chromosome\path
# return 1 if the result is a valid path and -1 otherwise
def mutation(chrom):
    # in average, one of the entire new population will have a mutation
    if not random.randint(0, NUM_CHILDREN):
        # generating "small" change: appending the path at a random point by single step (in the same direction)
        rand = random.randint(0, len(chrom.list_dir) - 1)
        chrom.list_dir = chrom.list_dir[:rand] + [chrom.list_dir[rand]] + chrom.list_dir[rand:]


if __name__ == "__main__":
    main()
