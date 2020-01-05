import belleroom
import cv2
import numpy as np

room = belleroom.BelleRoom("Cat", (1600, 900))
room.displayWhileDrawing = True
room.wiggle = True
catScene = belleroom.load_scene("cat")
cookingScene = belleroom.load_scene("cooking")
plateScene = belleroom.load_scene("plate")
sickScene = belleroom.load_scene("sick")
creditScene = belleroom.load_scene("credits")

room.delay(1)
room.draw_layer(catScene["Cat"], 2)
room.delay(0.8)
room.draw_layer(catScene["Eyes"], 1)
room.delay(1)
room.draw_layer(catScene["Beard"], 1)
room.delay(1)
room.clear()

room.draw_layer(cookingScene["Cat"], 1)
room.draw_layer(cookingScene["TV"], 1)
room.draw_layer(cookingScene["Chicken"], 1)
room.delay(2)
room.clear()

room.draw_layer(plateScene["Cat"], 1)
room.draw_layer(plateScene["Old"], 2)
room.draw_layer(plateScene["Meow"], 0.4)
room.draw_layer(plateScene["Plate"], 0.5)
room.delay(4)
room.clear()

room.draw_layer(sickScene["Old"], 2.5)
room.delay(0.5)
room.draw_layer(sickScene["Cat"], 1)
room.delay(0.5)
room.draw_layer(sickScene["Text"], 2)
room.delay(2)
room.clear()

room.draw_layer(creditScene["Text"], 3)
room.delay(2)

room.output("output.m4v", verbose=True)

cv2.destroyAllWindows()
