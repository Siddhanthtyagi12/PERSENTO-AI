# Game Development Education: Headshot Detection Logic
# This script is for educational purposes to understand how games like Free Fire 
# or other shooters handle "Headshot" detection.

import math

def check_headshot(hit_pos, target_head_center, head_radius, aim_assist_strength=0.0):
    """
    Simulates headshot detection with optional 'Aim Assist'.
    - head_radius: Bigger radius = easier headshots (Hitbox Scaling).
    - aim_assist_strength: Automatically moves the hit point closer to the head.
    """
    # Simulate Aim Assist (Pulling the shot towards the center)
    # This is how some "Safe" scripts work by slightly adjusting aim.
    effective_hit_pos = [
        hit_pos[0] + (target_head_center[0] - hit_pos[0]) * aim_assist_strength,
        hit_pos[1] + (target_head_center[1] - hit_pos[1]) * aim_assist_strength,
        hit_pos[2] + (target_head_center[2] - hit_pos[2]) * aim_assist_strength
    ]

    # Calculate distance
    distance = math.sqrt(
        (effective_hit_pos[0] - target_head_center[0])**2 + 
        (effective_hit_pos[1] - target_head_center[1])**2 + 
        (effective_hit_pos[2] - target_head_center[2])**2
    )
    
    if distance <= head_radius:
        return True, f"HEADSHOT! (Distance: {round(distance, 2)})"
    else:
        return False, f"Body Shot (Distance: {round(distance, 2)})"

# --- CASE 1: Normal Shot (Difficult) ---
player_hit = (100, 205, 50) 
enemy_head = (100, 200, 50)
radius = 2.0
success, msg = check_headshot(player_hit, enemy_head, radius)
print(f"Normal: {msg}")

# --- CASE 2: With Hitbox Scaling (Easier) ---
# Developers sometimes make hitboxes bigger for certain modes.
success, msg = check_headshot(player_hit, enemy_head, radius + 5.0) 
print(f"Bigger Hitbox: {msg}")

# --- CASE 3: With Aim Assist (Auto-Adjustment) ---
# The code 'pulls' the bullet towards the head.
# High strength = Short Range Aim Assist
success, msg = check_headshot(player_hit, enemy_head, radius, aim_assist_strength=0.8)
print(f"High Aim Assist (Short Range): {msg}")

# --- CASE 4: Perfect Aim (Aimbot logic) ---
# When strength is 1.0, the shot ALWAYS hits the center of the head.
# This works for any range (Long or Short) as it perfectly corrects the aim.
success, msg = check_headshot(player_hit, enemy_head, radius, aim_assist_strength=1.0)
print(f"Perfect Aim (Any Range): {msg}")

# ---------------------------------------------------------
# NOTE: 
# This is a basic mathematical model. 
# Cheating or hacking online games violates their terms of service 
# and can lead to permanent bans. Always play fair!
# ---------------------------------------------------------
