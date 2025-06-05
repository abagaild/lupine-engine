# Event: Chest
# Trigger: player_interact


def on_interact(player):
    print("You found a treasure!")


# Event trigger handling
def _ready():
    if hasattr(self, 'body_entered'):
        body_entered.connect(_on_body_entered)

def _on_body_entered(body):
    if body.name == "Player":
        if hasattr(self, 'on_interact'):
            on_interact(body)
