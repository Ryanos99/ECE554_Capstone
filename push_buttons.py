"""
Sources

Taken from https://stackoverflow.com/questions/67421759/equivalent-function-to-input-in-opencv-python

https://github.com/Xilinx/AUP-ZU3/blob/main/base/notebooks/video/opencv_face_detect_webcam.ipynb
https://github.com/Xilinx/PYNQ/blob/master/pynq/notebooks/arch/aarch64/common/display_port_introduction.ipynb
https://pynq.readthedocs.io/en/v2.0/pynq_package/pynq.lib/pynq.lib.button.html

"""



from pynq import Overlay
from pynq.lib.button import Button
import cv2
import string

overlay = Overlay("new.bit")

# TODO: Update these
PL_USER_PB0 = 0xAB6
PL_USER_PB1 = 0xAB7
PL_USER_PB2 = 0xAB2
PL_USER_PB3 = 0xAC6
REG_REP_CNT = 0x98
REG_EXERCISE = 0x9C

REG_REP_INCR = 0x22 # Do not know where this is

button_0 = Button(0)
button_1 = Button(1)
button_2 = Button(2)
button_3 = Button(3)

text = ""
is_typing = False
is_recording = False

# TODO: Change name as needed
workout_machine = overlay.workout_statemachine

class Stats:
    def __init__(self, name=""):
        self.name = name
        self.exercise_cnts = exercise_init.copy()
    
    def reset_count(self):
        self.exercise_cnts = exercise_init.copy()

    def set_name(self, new_name):
        self.name = new_name
    
    def set_exercise_cnts(self, exercise_to_set):
        self.exercise_cnts = exercise_to_set

    def to_string(self):
        the_string = self.name + ": "
        for key, value in self.exercise_cnts.items():
            the_string += f"{value} reps in " + CLASS_NAMES.get(key, "unknown") + ", "
        return the_string[:-2] # remove the trailing , 
    
    def copy(self):
        a_copy = Stats(self.name)
        a_copy.set_exercise_cnts(self.exercise_cnts)
        return a_copy

exercise_init = {'0': 0, '1': 0, '2': 0, '3': 0}
previous_stats = []
currentStat = Stats()
exercise_max = [None] * len(exercise_init.keys())

### TODO: The following code needs to be incorporated into pulse_monitor.py
### Hopefully you can just copy and paste everything into the while True loop
while True:
    key = cv2.waitKey(1) & 0xFF

    if (button_0.read()):
        # Current person reset
        currentStat.reset_count()
        for i in range(len(exercise_max)):
            if exercise_max[i] is not None and exercise_max[i][0] == currentStat.name:
                exercise_max[i] = None

    if (button_3.read()):
        # Global reset
        previous_stats = []
        currentStat = Stats()
        exercise_max = [None] * len(exercise_init.keys())

    if (button_1.read()):
        is_recording = True
        # Start the process
    
    if is_recording:
        if (workout_machine.read(REG_REP_INCR)):
            # Increment whichever workout
            currentStat.exercise_cnts[str(workout_machine.read(REG_EXERCISE))] += 1

    if (button_2.read() and is_recording):
        previous_stats.append(currentStat.copy())
        for i in range(len(exercise_max)):
            if exercise_max[i] is None or exercise_max[i][1] < currentStat.exercise_cnts[str(i)]:
                exercise_max[i] = (currentStat.name, currentStat.exercise_cnts[str(i)])

        currentStat = Stats()
        is_recording = False

    if (not(is_typing) and key == ord('q')):
        # Exiting....
        print("STATS...")
        for element in previous_stats:
            print(element.to_string())
        break

    if (not(is_typing) and key == ord('n')):
        # Create name
        text = ""
        is_typing = True

    if (is_typing):
        if (key == ord('\n') or key == ord('\r')):
            currentStat.set_name(text)
            is_typing = False
        elif chr(key) in string.printable:
            text += chr(key)

    # FIXME: Instead of adding this to the while loop, can it be added to draw_display?
    initial_x = 0
    initial_y = 160
    x_size = 300
    y_size = 320
    cv2.rectangle(frame, (initial_x, initial_y), (initial_x + x_size, initial_y + y_size), (0, 0, 0), -1)
    cv2.putText(frame, f"most recent player: {previous_stats[-1].to_string() if len(previous_stats) > 0 else 'N/A'}",
            (initial_x + 10, initial_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 1)
    
    for i in range(len(exercise_max)):
        cv2.putText(frame, f"Current best in {CLASS_NAMES.get(str(i), 'unknown')}: " + (f"{exercise_max[i][0]} with {exercise_max[i][1]}" if exercise_max[i] is not None else 'N/A'),
                    (initial_x + 10, initial_y + (i + 2) * 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        

# Displayport Code

from pynq.lib.video import *

displayport = DisplayPort()
displayport.configure(VideoMode(1920, 1080, 24), PIXEL_RGB)

### Add the following to the while True loop
dp_frame = displayport.newframe()
to_dp_frame = cv2.cvtColor(cv2.resize(frame, (1920, 1080)), cv2.COLOR_BGR2RGB)
dp_frame[:] = to_dp_frame
displayport.writeframe(dp_frame)


# At the end
displayport.close()
