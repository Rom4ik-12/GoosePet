import os
import sys
import random
import math
import tkinter as tk
from PIL import Image, ImageTk
import pyglet
from pyglet.media import Player, load

# Получаем путь к папке со скриптом
if getattr(sys, 'frozen', False):
    # Если приложение 'заморожено' (упаковано в exe)
    script_dir = os.path.dirname(sys.executable)
else:
    # Обычный режим выполнения скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
print(script_dir)
# Функция для создания абсолютных путей
def resource_path(relative_path):
    return os.path.join(script_dir, relative_path)

# Создаем папки если их нет
os.makedirs(resource_path("goose_animations/idle"), exist_ok=True)
os.makedirs(resource_path("goose_animations/walk"), exist_ok=True)
os.makedirs(resource_path("goose_animations/jump"), exist_ok=True)
os.makedirs(resource_path("sounds"), exist_ok=True)

# Загрузка анимаций с правильными путями
def load_animation(folder):
    frames = []
    full_folder_path = resource_path(folder)  # Преобразуем относительный путь в абсолютный
    print(f"Загрузка анимаций из: {full_folder_path}")  # Отладочный вывод
    
    try:
        files = sorted([f for f in os.listdir(full_folder_path) if f.endswith('.png')])
        print(f"Найдены файлы: {files}")  # Отладочный вывод
        
        for file in files:
            try:
                full_file_path = os.path.join(full_folder_path, file)
                print(f"Загрузка: {full_file_path}")  # Отладочный вывод
                frame = Image.open(full_file_path).convert("RGBA")
                frames.append(frame)
            except Exception as e:
                print(f"Ошибка загрузки {file}: {e}")
                continue
    except Exception as e:
        print(f"Ошибка доступа к папке {full_folder_path}: {e}")
    
    if not frames:
        print("Анимации не найдены, создаём заглушку")
        dummy = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        for x in range(80):
            for y in range(80):
                if (x-40)**2 + (y-40)**2 <= 1600:  # Круг
                    dummy.putpixel((x, y), (255, 255, 0, 255))
        frames = [dummy]
    
    return frames
    
    if not frames:
        # Создаем заглушку
        dummy = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        for x in range(80):
            for y in range(80):
                if (x-40)**2 + (y-40)**2 <= 1600:  # Круг
                    dummy.putpixel((x, y), (255, 255, 0, 255))
        frames = [dummy]
    
    return frames

# Загрузка звуков с правильными путями
def load_sound(filename, volume=1.0):
    try:
        sound = load(resource_path(f"sounds/{filename}"), streaming=False)
        sound.volume = volume
        return sound
    except:
        return None

# Инициализация звуков с настройкой громкости
sound_step = load_sound("step.wav")
sound_jump = load_sound("jump.wav")
sound_quack = load_sound("quack.wav")

# Создаем главное окно
root = tk.Tk()
root.attributes('-alpha', 1.0)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.config(bg='black')
root.wm_attributes('-transparentcolor', 'black')

# Холст для рисования
canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), 
                   bg='black', highlightthickness=0)
canvas.pack()

# Загружаем анимации с правильными путями
animations = {
    "idle": load_animation(resource_path("goose_animations/idle")),
    "walk": load_animation(resource_path("goose_animations/walk")),
    "jump": load_animation(resource_path("goose_animations/jump"))
}


# Параметры гуся
current_state = "walk"
current_frame = 0
animation_speed = 0.15
goose_width, goose_height = animations["walk"][0].size
goose_x = random.randint(100, root.winfo_screenwidth()-100)
goose_y = random.randint(100, root.winfo_screenheight()-100)

# Физика движения
speed = random.uniform(1.0, 2.5)
direction = random.uniform(0, 2*math.pi)
facing_right = True

# Прыжки
is_jumping = False
jump_height = 0
max_jump_height = 60
jump_progress = 0
jump_cooldown = 0
has_played_jump_sound = False

# Звуки шагов
step_timer = 0
step_interval = 0.35

# Кряканье
quack_timer = 0
quack_interval = random.uniform(5, 15)

# Игровые переменные
last_time = 0
goose_image = None
goose_image_id = None

def update(dt):
    global current_state, current_frame, goose_x, goose_y, direction, speed, facing_right
    global is_jumping, jump_height, jump_progress, jump_cooldown, has_played_jump_sound
    global step_timer, quack_timer, quack_interval, goose_image, goose_image_id, step_interval
    
    # Удаляем предыдущее изображение
    if goose_image_id:
        canvas.delete(goose_image_id)
    
    # Случайное изменение направления
    if random.random() < 0.01:
        direction = random.uniform(0, 2*math.pi)
        speed = random.uniform(1.0, 2.5)
    
    # Прыжки
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
    
    # Движение
    prev_x, prev_y = goose_x, goose_y
    goose_x += math.cos(direction) * speed * 60 * dt
    goose_y += math.sin(direction) * speed * 60 * dt
    
    # Звуки шагов
    if not is_jumping and speed > 0.5:
        step_timer += dt
        distance_moved = math.hypot(goose_x - prev_x, goose_y - prev_y)
        
        if step_timer >= step_interval and distance_moved > 2 and sound_step:
            sound_step.play()
            step_timer = 0
            step_interval = random.uniform(0.3, 0.4)
    
    # Случайное кряканье
    quack_timer += dt
    if quack_timer >= quack_interval and sound_quack:
        sound_quack.play()
        quack_timer = 0
        quack_interval = random.uniform(5, 15)
    
    # Определение направления
    facing_right = math.cos(direction) > 0
    
    # Отскок от границ
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
    
    # Выбор анимации
    if is_jumping:
        current_state = "jump"
    elif speed > 0.5:
        current_state = "walk"
    else:
        current_state = "idle"
    
    # Анимация
    current_frame += animation_speed
    if current_frame >= len(animations[current_state]):
        current_frame = 0
    
    # Получаем текущий кадр
    frame = animations[current_state][int(current_frame) % len(animations[current_state])]
    
    if not facing_right:
        frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
    
    # Отображаем изображение
    goose_image = ImageTk.PhotoImage(frame)
    goose_image_id = canvas.create_image(goose_x, goose_y - jump_height, image=goose_image, anchor='nw')
    
    # Планируем следующий кадр
    root.after(16, lambda: update(0.016))

# Запускаем игру
root.after(0, lambda: update(0))
root.mainloop()