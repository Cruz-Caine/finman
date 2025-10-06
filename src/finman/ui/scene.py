import curses # imports curses a barebones highly portable tui library

class Scene():
    def __init__(self,screen,pred_scene):
        self.change_scene = None
        self.pred_scene = pred_scene
        self.screen = screen
        pass

    def handle_input(self,input):
        pass

    def update(self):
        pass

    def render(self):
        pass

    def full_pass(self,input):
        self.handle_input(input)
        scene = self.update()
        self.render()
        return scene

    def on_enter(self):
        pass

    def on_exit(self):
        self.change_scene = None
        pass



