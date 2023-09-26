from tkinter import BOTH, YES, Tk, Canvas
from typing import List, Dict, Any
import sys
from random import randint, uniform, gauss
import math
from abc import ABC, abstractmethod
from copy import deepcopy

# TODO: Define FaceContext
FaceContext = Dict[str, Any]
INTERVAL = 33


class FaceModifier(ABC):
    @abstractmethod
    def apply(self, interval: int, face_context: FaceContext) -> FaceContext:
        pass


class BlinkModifier(FaceModifier):
    def __init__(self, open_min: int, open_max: int, close_min: int,
                 close_max: int):
        self.open_min = open_min
        self.open_max = open_max
        self.close_min = close_min
        self.close_max = close_max
        self.is_blinking = False
        self.next_toggle = randint(self.open_min, self.open_max)
        self.count = 0

    def linear_in_ease_out(self, fraction: float) -> float:
        if fraction < 0.25:
            return 1 - fraction * 4
        else:
            return (pow(fraction - 0.25, 2) * 16) / 9

    def apply(self, interval: int, face_context: FaceContext) -> FaceContext:
        eye_open = 1.0
        if self.is_blinking:
            fraction = self.linear_in_ease_out(self.count / self.next_toggle)
            eye_open = 0.2 + fraction * 0.8

        self.count += interval
        if self.count >= self.next_toggle:
            self.is_blinking = not self.is_blinking
            self.count = 0
            if self.is_blinking:
                self.next_toggle = randint(
                    self.close_min, self.close_max)
            else:
                self.next_toggle = randint(
                    self.open_min, self.open_max)

        for eye in face_context['eyes'].values():
            eye['open'] *= eye_open

        return face_context


class SaccadeModifier(FaceModifier):
    def __init__(self, update_min: int, update_max: int, gain: float):
        self.update_min = update_min
        self.update_max = update_max
        self.gain = gain
        self.next_toggle = uniform(self.update_min, self.update_max)
        self.saccade_x = 0
        self.saccade_y = 0

    def apply(self, tick_millis: int, face: FaceContext) -> FaceContext:
        self.next_toggle -= tick_millis
        if self.next_toggle < 0:
            self.saccade_x = gauss(0, self.gain)
            self.saccade_y = gauss(0, self.gain)
            self.next_toggle = uniform(self.update_min, self.update_max)

        for eye in face['eyes'].values():
            eye['gazeX'] += self.saccade_x
            eye['gazeY'] += self.saccade_y

        return face


class BreathModifier(FaceModifier):
    def __init__(self, duration: int):
        self.duration = duration
        self.time = 0

    def apply(self, tick_millis: int, face: FaceContext) -> FaceContext:
        self.time += tick_millis % self.duration
        face['breath'] = round(
            math.sin((2 * math.pi * self.time) / self.duration), 8)
        return face


class FaceRenderer:
    def __init__(self, canvas: Canvas, face_context: Dict[str, Any]) -> None:
        self.canvas = canvas
        self.original_width = canvas.winfo_width()
        self.original_height = canvas.winfo_height()
        self.current_context = face_context
        self.all_objects: List[int] = []
        self.modifiers: List[FaceModifier] = []
        self.set_origin(320 // 2, 240 // 2)
        self.set_scale(1.0, 1.0)

    def set_origin(self, cx, cy):
        self.cx = cx
        self.cy = cy

    def set_scale(self, scale_x, scale_y):
        self.scale_x = scale_x
        self.scale_y = scale_y

    def add_modifier(self, modifier: FaceModifier) -> None:
        self.modifiers.append(modifier)

    def draw_eyes(self, cx: int, cy: int, radius: int,
                  eye_context: Dict[str, float]):
        scale = min(self.scale_x, self.scale_y)
        cx = self.cx + (cx - 160) * scale
        cy = self.cy + (cy - 120) * scale
        radius *= scale
        gaze_x = eye_context.get('gazeX', 0) * 2
        gaze_y = eye_context.get('gazeY', 0) * 2

        pupil_id = self.canvas.create_oval(
            cx + gaze_x - radius,
            cy + gaze_y - radius,
            cx + gaze_x + radius,
            cy + gaze_y + radius,
            fill='white')

        eyelid_cover = (1 - eye_context['open']) * 2 * radius
        if eyelid_cover > 0.1:
            eyelid_id = self.canvas.create_rectangle(
                cx - radius,
                cy - radius,
                cx + radius,
                cy - radius + eyelid_cover,
                fill='black')
            self.all_objects.extend([pupil_id, eyelid_id])
        else:
            self.all_objects.extend([pupil_id])

    def draw_mouth(self, cx: int, cy: int, minWidth: int, maxWidth: int,
                   minHeight: int, maxHeight: int,
                   mouth_context: Dict[str, float]) -> None:
        scale = min(self.scale_x, self.scale_y)
        cx = self.cx + (cx - 160) * scale
        cy = self.cy + (cy - 120) * scale
        minWidth *= scale
        maxWidth *= scale
        minHeight *= scale
        maxHeight *= scale
        openRatio = mouth_context['open']
        h = minHeight + (maxHeight - minHeight) * openRatio
        w = minWidth + (maxWidth - minWidth) * (1 - openRatio)
        x = cx - w / 2
        y = cy - h / 2
        mouth_id = self.canvas.create_rectangle(
            x, y, x + w, y + h, fill='white')
        self.all_objects.append(mouth_id)

    def move_face(self, dy: float) -> None:
        for obj_id in self.all_objects:
            self.canvas.move(obj_id, 0, dy)

    def update(self, interval: int) -> None:
        context = deepcopy(self.current_context)
        for modifier in self.modifiers:
            context = modifier.apply(interval, context)
        self.render(context)

    def render(self, context: FaceContext) -> None:
        self.canvas.delete("all")
        self.all_objects = []

        left_eye_coords = {'cx': 90, 'cy': 93, 'radius': 8}
        right_eye_coords = {'cx': 230, 'cy': 96, 'radius': 8}
        mouth_coords = {'cx': 160, 'cy': 148, 'minWidth': 50,
                        'maxWidth': 90, 'minHeight': 8, 'maxHeight': 58}

        self.draw_eyes(**left_eye_coords, eye_context=context['eyes']['left'])
        self.draw_eyes(**right_eye_coords,
                       eye_context=context['eyes']['right'])
        self.draw_mouth(**mouth_coords, mouth_context=context['mouth'])

        dy = context['breath'] * 3 * min(self.scale_x, self.scale_y)
        self.move_face(dy)


default_context = {
    'mouth': {'open': 0.0},
    'eyes': {
        'left': {'gazeX': 0.0, 'gazeY': 0.0, 'open': 1.0},
        'right': {'gazeX': 0.0, 'gazeY': 0.0, 'open': 1.0},
    },
    'breath': 0,
}


class AvatarFace():
    def __init__(self, root):
        self.root = root
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.canvas = canvas = Canvas(root, width=320, height=240, bg='black')
        self.canvas.pack(fill=BOTH, expand=YES)
        self.face_renderer = face_renderer = FaceRenderer(
            canvas, default_context)
        self.running = False
        self.is_closed = False
        blink_modifier = BlinkModifier(
            open_min=400, open_max=5000, close_min=200, close_max=400)
        breath_modifier = BreathModifier(duration=6000)
        saccade_modifier = SaccadeModifier(
            update_min=300, update_max=2000, gain=0.2)

        face_renderer.add_modifier(blink_modifier)
        face_renderer.add_modifier(breath_modifier)
        face_renderer.add_modifier(saccade_modifier)

    def is_alive(self):
        return not (self.is_closed)

    def on_closing(self):
        self.is_closed = True
        self.root.quit()

    def on_resize(self, event):
        self.canvas.delete('all')
        w, h = event.width, event.height
        self.face_renderer.set_origin(w // 2, h // 2)
        self.face_renderer.set_scale(w / 320, h / 240)

    def set_mouth_open(self, open):
        if open < 0 or math.isnan(open):
            open = 0
        if open > 1.0:
            open = 1.0
        self.face_renderer.current_context['mouth']['open'] = open

    def begin(self):
        self.running = True
        self.loop()
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.quit()

    def loop(self, interval=INTERVAL):
        if not self.running:
            return
        self.face_renderer.update(INTERVAL)
        self.root.after(INTERVAL, self.loop)


if __name__ == "__main__":
    def exit_program(event):
        sys.exit(0)

    root = Tk()
    root.bind('<Control-c>', exit_program)
    avatar: AvatarFace = AvatarFace(root)
    avatar.begin()
