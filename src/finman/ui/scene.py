import curses # imports curses a barebones highly portable tui library

class Scene():
    def __init__(self,screen):
        pass

    def handle_input(self,input):
        pass

    def update(self,scene):
        pass

    def render(self):
        pass

    def full_pass(self,input,scene):
        self.handle_input(input)
        self.update(scene)
        self.render()

    def on_enter(self):
        pass

    def on_exit(self):
        pass



