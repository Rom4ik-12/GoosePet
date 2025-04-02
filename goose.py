import os
import sys
import random
import math
import tkinter as tk
from PIL import Image, ImageTk
import pyglet
from pyglet.media import Player, load
import time

# Получаем путь к папке со скриптом
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    return os.path.join(script_dir, relative_path)

# Создаем папки если их нет
os.makedirs(resource_path("goose_animations/idle"), exist_ok=True)
os.makedirs(resource_path("goose_animations/walk"), exist_ok=True)
os.makedirs(resource_path("goose_animations/jump"), exist_ok=True)
os.makedirs(resource_path("goose_animations/pet"), exist_ok=True)
os.makedirs(resource_path("sounds"), exist_ok=True)

# Кэш для изображений
photo_cache = {}

def load_and_cache_animation(folder_name, folder_path):
    frames = []
    full_folder_path = resource_path(folder_path)
    
    try:
        files = sorted([f for f in os.listdir(full_folder_path) if f.endswith('.png')])
        for i, file in enumerate(files):
            try:
                frame = Image.open(os.path.join(full_folder_path, file)).convert("RGBA")
                frames.append(frame)
                photo_cache[f"{folder_name}_{i}"] = ImageTk.PhotoImage(frame)
                photo_cache[f"{folder_name}_{i}_flipped"] = ImageTk.PhotoImage(frame.transpose(Image.FLIP_LEFT_RIGHT))
            except Exception as e:
                print(f"Error loading {file}: {e}")
                continue
    except Exception as e:
        print(f"Error accessing folder {full_folder_path}: {e}")
    
    if not frames:
        dummy = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        for x in range(80):
            for y in range(80):
                if (x-40)**2 + (y-40)**2 <= 1600:
                    dummy.putpixel((x, y), (255, 255, 0, 255))
        frames = [dummy]
        photo_cache[f"{folder_name}_0"] = ImageTk.PhotoImage(dummy)
        photo_cache[f"{folder_name}_0_flipped"] = ImageTk.PhotoImage(dummy.transpose(Image.FLIP_LEFT_RIGHT))
    
    return frames

def load_sound(filename, volume=1.0):
    try:
        sound = load(resource_path(f"sounds/{filename}"), streaming=False)
        sound.volume = volume
        return sound
    except Exception as e:
        print(f"Error loading sound {filename}: {e}")
        return None

# Инициализация звуков
sound_step = load_sound("step.wav")
sound_jump = load_sound("jump.wav")
sound_quack = load_sound("quack.wav")
sound_pet = load_sound("pet.wav")

# Создаем главное окно
root = tk.Tk()
root.attributes('-alpha', 1.0)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.config(bg='black')
root.wm_attributes('-transparentcolor', 'black')

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), 
                   bg='black', highlightthickness=0)
canvas.pack()

# Загружаем анимации
animations = {
    "idle": load_and_cache_animation("idle", "goose_animations/idle"),
    "walk": load_and_cache_animation("walk", "goose_animations/walk"),
    "jump": load_and_cache_animation("jump", "goose_animations/jump"),
    "pet": load_and_cache_animation("pet", "goose_animations/pet")
}

# Параметры гуся
current_state = "idle"
current_frame = 0
animation_speed = 0.15
goose_width, goose_height = 80, 80
if animations["walk"]:
    goose_width, goose_height = animations["walk"][0].size

goose_x = random.randint(100, root.winfo_screenwidth()-100)
goose_y = random.randint(100, root.winfo_screenheight()-100)

# Физика движения
speed = 0
direction = random.uniform(0, 2*math.pi)
facing_right = True

# Прыжки
is_jumping = False
jump_height = 0
max_jump_height = 60
jump_progress = 0
jump_cooldown = 0
has_played_jump_sound = False

# Поглаживание
is_petting = False
pet_progress = 0
pet_duration = 2.0
pet_cooldown = 0

# Таймеры поведения
behavior_timer = 0
idle_duration = random.uniform(2, 5)
walk_duration = random.uniform(3, 8)

# Звуки шагов
step_timer = 0
step_interval = 0.35

# Кряканье
quack_timer = 0
quack_interval = random.uniform(5, 15)

# Игровые переменные
goose_image_id = None
last_frame_time = time.time()

def handle_click(event):
    global is_petting, pet_progress, current_state, pet_cooldown
    
    if pet_cooldown <= 0 and (goose_x <= event.x <= goose_x + goose_width and 
                             goose_y <= event.y <= goose_y + goose_height):
        is_petting = True
        pet_progress = 0
        current_state = "pet"
        pet_cooldown = 3.0
        if sound_pet:
            sound_pet.play()

def update():
    global current_state, current_frame, goose_x, goose_y, direction, speed, facing_right
    global is_jumping, jump_height, jump_progress, jump_cooldown, has_played_jump_sound
    global step_timer, quack_timer, quack_interval, goose_image_id, step_interval
    global is_petting, pet_progress, pet_cooldown, last_frame_time
    global behavior_timer, idle_duration, walk_duration
    
    current_time = time.time()
    dt = current_time - last_frame_time
    last_frame_time = current_time
    dt = min(dt, 0.1)
    
    if goose_image_id:
        canvas.delete(goose_image_id)
    
    behavior_timer += dt
    pet_cooldown -= dt
    
    # Автоматическое изменение поведения
    if current_state == "idle" and behavior_timer >= idle_duration:
        current_state = "walk"
        speed = random.uniform(1.0, 2.5)
        direction = random.uniform(0, 2*math.pi)
        behavior_timer = 0
        walk_duration = random.uniform(3, 8)
    elif current_state == "walk" and behavior_timer >= walk_duration:
        current_state = "idle"
        speed = 0
        behavior_timer = 0
        idle_duration = random.uniform(2, 5)
    
    if current_state == "walk" and random.random() < 0.05:
        direction += random.uniform(-0.5, 0.5)
    
    # Обработка поглаживания
    if is_petting:
        pet_progress += dt
        if pet_progress >= pet_duration:
            is_petting = False
            current_state = "idle"
    
    # Физика и звуки
    if not is_petting:
        if current_state == "walk":
            jump_cooldown -= dt
            if not is_jumping and jump_cooldown <= 0 and random.random() < 0.02:
                is_jumping = True
                jump_progress = 0
                jump_cooldown = random.uniform(3, 8)
                has_played_jump_sound = False
                if sound_jump:
                    sound_jump.play()
        
        if is_jumping:
            jump_progress += dt * 3
            if not has_played_jump_sound and jump_progress > 0.1 and sound_jump:
                sound_jump.play()
                has_played_jump_sound = True
            if jump_progress >= math.pi:
                is_jumping = False
            jump_height = math.sin(jump_progress) * max_jump_height
        
        if current_state == "walk":
            prev_x, prev_y = goose_x, goose_y
            goose_x += math.cos(direction) * speed * 60 * dt
            goose_y += math.sin(direction) * speed * 60 * dt
            
            if not is_jumping and speed > 0.5:
                step_timer += dt
                distance_moved = math.hypot(goose_x - prev_x, goose_y - prev_y)
                if step_timer >= step_interval and distance_moved > 2 and sound_step:
                    sound_step.play()
                    step_timer = 0
                    step_interval = random.uniform(0.3, 0.4)
        
        quack_timer += dt
        if quack_timer >= quack_interval and sound_quack:
            sound_quack.play()
            quack_timer = 0
            quack_interval = random.uniform(5, 15)
        
        if current_state == "walk":
            facing_right = math.cos(direction) > 0
            
            if goose_x < 0:
                direction = math.pi - direction
                goose_x = 0
                facing_right = True
            elif goose_x > root.winfo_screenwidth() - goose_width:
                direction = math.pi - direction
                goose_x = root.winfo_screenwidth() - goose_width
                facing_right = False
            
            if goose_y < 0:
                direction = -direction
                goose_y = 0
            elif goose_y > root.winfo_screenheight() - goose_height:
                direction = -direction
                goose_y = root.winfo_screenheight() - goose_height
    
    # Анимация
    current_frame += animation_speed * 60 * dt
    if animations[current_state]:
        current_frame %= len(animations[current_state])
    
    frame_index = int(current_frame)
    cache_key = f"{current_state}_{frame_index}{'' if facing_right or current_state in ['idle', 'pet'] else '_flipped'}"
    
    current_image = photo_cache.get(cache_key)
    if current_image:
        goose_image_id = canvas.create_image(goose_x, goose_y - jump_height, 
                                          image=current_image, 
                                          anchor='nw')
    
    root.after(1, update)

# Привязываем обработчик клика
canvas.bind("<Button-1>", handle_click)

# Запускаем игру
update()
root.mainloop()