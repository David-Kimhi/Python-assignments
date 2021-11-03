from tkinter import *
import operator
import threading
import time

BUTTON_BAR_HEIGHT = 60

SELECTED = 1
NON_SELECTED = 0
START = 11
END = 12
PATH = 3


YELLOW_COLOR = (255, 255, 0)
RED_COLOR = (255, 0, 0)

class Cell:
    SELECTED_COLOR_BG = "white"
    SELECTED_COLOR_BORDER = "black"
    NON_SELECTED_COLOR_BG = "blue"
    NON_SELECTED_COLOR_BORDER = "black"

    PATH_COLOR_BG = "yellow"
    PATH_COLOR_BORDER = "orange"
    FINISH_COLOR_BG = "brown"

    STARTING_COLOR_BG = "green"
    ENDING_COLOR_BG = "purple"

    def __init__(self, master, i, j, n, width, height):
        self.master = master
        self.i = i
        self.j = j
        self.n = n
        self.state = NON_SELECTED
        self.width = width
        self.height = height

        self.has_path = 0
        self.yellow_color = YELLOW_COLOR
        self.red_color = RED_COLOR

    def set_state(self, state):
        self.state = state

    def draw(self, color=None):
        if self.master is None:
            return

        if self.master.mode == "erase":
            if self.state == SELECTED:
                self.state = NON_SELECTED

        elif self.master.mode == "draw":
            if self.state == NON_SELECTED:
                self.state = SELECTED

        elif self.master.mode == "start_end":
            if not self.master.has_start:
                self.state = START
                self.master.has_start = True
                self.master.s_point = (self.i, self.j)
            elif (not self.master.has_end) and (self.i, self.j != self.master.s_point):
                self.state = END
                self.master.has_end = True
                self.master.e_point = (self.i, self.j)

                self.master.button_run['state'] = self.master.button_draw['state'] = NORMAL
                self.master.button_place['state'] = self.master.button_erase['state'] = DISABLED

        bg_color = Cell.NON_SELECTED_COLOR_BG
        border_color = Cell.NON_SELECTED_COLOR_BORDER

        if self.state == SELECTED:
            bg_color = Cell.SELECTED_COLOR_BG
            border_color = Cell.SELECTED_COLOR_BORDER
        elif self.state == PATH:
            bg_color = color
            border_color = Cell.PATH_COLOR_BORDER
        elif self.state == START:
            bg_color = Cell.STARTING_COLOR_BG
        elif self.state == END:
            bg_color = Cell.ENDING_COLOR_BG

        x_start = self.i * self.width
        x_end = x_start + self.width
        y_start = self.j * self.height
        y_end = y_start + self.height

        self.master.create_rectangle(x_start, y_start, x_end, y_end, fill=bg_color, outline=border_color)


class CellGrid(Canvas):
    def __init__(self, master, monitor, n, **kwargs):
        Canvas.__init__(self, master, **kwargs)

        self.monitor = monitor
        self.n = n
        self.width = int(self["width"])
        self.height = int(self["height"])
        self.cell_width = int(self.width / n)
        self.cell_height = int((self.height - BUTTON_BAR_HEIGHT) / n)
        self.grid = []
        self.s_point = self.e_point = (0, 0)

        for row in range(n):
            line = []
            for col in range(n):
                line.append(Cell(self, row, col, n, self.cell_width, self.cell_height))

            self.grid.append(line)

        self.mode = "none"
        self.has_start = self.has_end = False

        self.bind("<Button-1>", self.mouse_click)
        self.bind("<B1-Motion>", self.mouse_else)
        self.bind("<ButtonRelease-1>", self.mouse_else)

        b_relwidth = 0.2
        button_width = int(b_relwidth*self.width)

        fixed_y = int(self.cell_height * n) + 3
        self.button_run = Button(self, text="Run", command=self.run)
        self.button_run.place(x=0, y=fixed_y, relwidth=b_relwidth, height=BUTTON_BAR_HEIGHT)

        self.button_draw = Button(self, text="Draw Obstacles", command=self.draw_o)
        self.button_draw.place(x=button_width, y=fixed_y, relwidth=b_relwidth, height=BUTTON_BAR_HEIGHT)

        self.button_erase = Button(self, text="Erase Obstacles", command=self.erase_o)
        self.button_erase.place(x=button_width * 2, y=fixed_y, relwidth=b_relwidth, height=BUTTON_BAR_HEIGHT)

        self.button_place = Button(self, text="Place Points", command=self.start_end)
        self.button_place.place(x=button_width * 3, y=fixed_y, relwidth=b_relwidth, height=BUTTON_BAR_HEIGHT)

        self.button_clear = Button(self, text="Clear and restart", command=self.clear)
        self.button_clear.place(x=button_width * 4, y=fixed_y, relwidth=b_relwidth, height=BUTTON_BAR_HEIGHT)

        self.button_run['state'] = self.button_draw['state'] = self.button_erase['state'] = self.button_clear['state']\
            = DISABLED
        self.draw()

        # ****** status bar *****
        self.message = StringVar()
        self.message.set("Ready")
        self.status = Label(self.master, textvariable= self.message, bd=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=TOP, fill=X)

    def draw(self):
        for i in self.grid:
            for j in i:
                j.draw()

    def _event_coordinates(self, event):
        row = int(event.x / self.cell_width)
        column = int(event.y / self.cell_height)
        if row < 0:
            row = 0
        elif row >= self.n:
            row = self.n-1
        if column < 0:
            column = 0
        elif column >= self.n:
            column = self.n-1

        return row, column

    def mouse_else(self, event):
        if self.mode != "start_end":
            row, col = self._event_coordinates(event)
            cell = self.grid[row][col]
            cell.draw()

    def mouse_click(self, event):
        row, col = self._event_coordinates(event)
        cell = self.grid[row][col]
        cell.draw()

    def draw_o(self):
        self.mode = "draw"
        self.button_draw['state'] = DISABLED
        self.button_erase['state'] = NORMAL
        self.change_status("Click and drag your mouse to draw obstacles in the grid")

    def erase_o(self):
        self.mode = "erase"
        self.button_draw['state'] = NORMAL
        self.button_erase['state'] = DISABLED
        self.change_status("Click and drag your mouse to erase the obstacles")

    def start_end(self):
        self.mode = "start_end"
        self.button_clear['state'] = NORMAL
        self.change_status("Click once to place the starting point. Click again to place the ending point")

    def clear(self):
        self.change_status("Clearing...")
        self.update()
        self.mode = "erase"
        self.has_start = self.has_end = False
        self.button_run['state'] = self.button_draw['state'] = self.button_erase['state'] = self.button_clear['state']\
            = DISABLED
        self.button_place['state'] = NORMAL
        for row in self.grid:
            for cell in row:
                cell.state = SELECTED
                cell.draw()
        self.mode = "none"

        self.change_status("Ready")

        self.monitor.clear()

    def run(self):
        self.button_draw['state'] = self.button_erase['state'] = self.button_place['state'] = self.button_run['state']\
            = self.button_clear['state'] = DISABLED
        self.mode = "running"
        self.change_status("Running...")
        self.send_grid()

    def send_grid(self):
        grid = []
        for row in range(len(self.grid)):
            grid.append([])
            for col in range(len(self.grid[0])):
                grid[row].append(self.grid[row][col].state)

        self.monitor.run(grid, self.s_point, self.e_point)

    def change_status(self, message):
        self.message.set(message)

    def show_generations(self, pool):
        for chrom in pool:
            self.show_chrom(chrom)

    def show_chrom(self, chrom):
        """
        show a single chromosome's path on the grid
        :param chrom: the chromosome to show
        :return: None
        """

        for point in chrom.set_points:
            cell = self.grid[point[0]][point[1]]        # locate the matching cell on the grid
            if cell.state != START and cell.state != END:
                if cell.state == NON_SELECTED:
                    cell.state = PATH

                subtract = 5
                a = max(0, cell.yellow_color[0] - subtract)
                b = max(0, cell.yellow_color[1] - subtract)

                cell.yellow_color = (a, b, 0)
                color = rgb_to_hex(cell.yellow_color)
                cell.has_path += 1
                cell.draw(color)

    def clear_chrom(self, chrom):
        for point in chrom.set_points:
            cell = self.grid[point[0]][point[1]]
            if cell.state != START and cell.state != END:
                if cell.has_path == 1:
                    cell.state = NON_SELECTED
                add = 5
                a = min(255, cell.yellow_color[0] + add)
                b = min(255, cell.yellow_color[1] + add)
                cell.yellow_color = (a, b, 0)

                color = rgb_to_hex(cell.yellow_color)
                cell.draw(color)

            cell.has_path = max(0, cell.has_path - 1)


def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb
