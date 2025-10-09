import curses # imports curses a barebones highly portable tui library

class Scene():
    def __init__(self,screen,pred_scene):
        self.change_scene = None
        self.pred_scene = pred_scene
        self.screen = screen
        self.needs_render = True  # Flag to track if rendering is needed
        pass

    def handle_input(self,input):
        pass

    def update(self):
        pass

    def render(self):
        pass

    def full_pass(self,input):
        # Only process input and mark for render if there's actual input
        if input != -1:  # -1 means no input (nodelay mode)
            # Handle terminal resize
            if input == curses.KEY_RESIZE:
                self.needs_render = True
            else:
                self.handle_input(input)
                self.needs_render = True

        # Only update and render when needed
        scene = None
        if self.needs_render or self.change_scene is not None:
            scene = self.update()
            if self.needs_render:
                self.render()
                self.needs_render = False

        return scene

    def on_enter(self):
        self.needs_render = True  # Force render when entering scene
        pass

    def on_exit(self):
        self.change_scene = None
        pass



