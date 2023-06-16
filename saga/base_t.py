def execute(self, starting_step = None):
    if starting_step is None:
        current_step = self.steps[0]

    while True:
        current_step.execute()
        current_step = next(current_step)








