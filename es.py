import pymem
import pymem.process
import ctypes
from ctypes import wintypes
import time
import math
import os
import sys

# ------------------------------------------------------------------
# OFFSETS (CS2 as of 2026-06-29) - UPDATE on every game patch
# ------------------------------------------------------------------
# client.dll base offsets
dwLocalPlayer         = 0xDEA964          # client.dll + offset -> local player controller
dwEntityList          = 0xDF2F38          # client.dll + offset -> entity list (radar struct)
dwViewMatrix          = 0x1B3D5A0         # client.dll + offset -> view matrix for W2S
dwGlowObjectManager   = 0xDFB898          # not used, kept for reference
dwForceJump           = 0xDFC7B0          # not used

# Offsets for C_CSPlayerPawn (base entity)
m_iHealth             = 0x334             # int32 health
m_vOldOrigin          = 0x1280            # Vector3 position (feet)
m_vecViewOffset       = 0x1098            # Vector3 view offset (for head)
m_iTeamNum            = 0x3C3             # int32 team (2 = Terrorist, 3 = CT)
m_bDormant            = 0xE9D             # bool (skip if dormant)
m_pGameSceneNode      = 0x310             # pointer to scene node (not used)
m_modelState          = 0x170             # inside scene node (not used)

# Offsets for local player controller
m_hPlayerPawn         = 0x7EC             # pawn handle in controller

# Entity list entry structure (radar)
m_pEntity             = 0x10              # pointer to entity inside radar struct
# ------------------------------------------------------------------

def get_client_module():
    """Returns Pymem object and base address of client.dll"""
    try:
        pm = pymem.Pymem("cs2.exe")
        module = pymem.process.module_from_name(pm.process_handle, "client.dll")
        return pm, module.lpBaseOfDll
    except Exception as e:
        # Silent fail to avoid console output
        return None, 0

def read_vector3(pm, address):
    """Reads a Vector3 (3 floats) from memory"""
    data = pm.read_bytes(address, 12)
    x = ctypes.c_float.from_buffer_copy(data[0:4]).value
    y = ctypes.c_float.from_buffer_copy(data[4:8]).value
    z = ctypes.c_float.from_buffer_copy(data[8:12]).value
    return (x, y, z)

def world_to_screen(view_matrix, pos, screen_width, screen_height):
    """Transforms world position to screen coordinates"""
    w = pos[0]*view_matrix[3] + pos[1]*view_matrix[7] + pos[2]*view_matrix[11] + view_matrix[15]
    if w < 0.001:
        return None
    x = pos[0]*view_matrix[0] + pos[1]*view_matrix[4] + pos[2]*view_matrix[8] + view_matrix[12]
    y = pos[0]*view_matrix[1] + pos[1]*view_matrix[5] + pos[2]*view_matrix[9] + view_matrix[13]
    inv_w = 1.0 / w
    x *= inv_w
    y *= inv_w
    screen_x = (screen_width / 2) * (1 + x)
    screen_y = (screen_height / 2) * (1 - y)
    return (int(screen_x), int(screen_y))

def draw_overlay(screen_pos, health, team):
    """Placeholder for drawing. In real use, use win32gui/DirectX.
       Here we write to a file for demonstration."""
    with open("esp_log.txt", "a") as f:
        f.write(f"{time.time()} X:{screen_pos[0]} Y:{screen_pos[1]} HP:{health} TEAM:{team}\n")

def main_loop():
    pm, client_base = get_client_module()
    if not pm:
        sys.exit(0)  # Silent exit

    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    while True:
        try:
            local_controller_addr = client_base + dwLocalPlayer
            local_controller = pm.read_int(local_controller_addr)
            if not local_controller:
                time.sleep(0.005)
                continue

            view_matrix = pm.read_float(client_base + dwViewMatrix, 16)

            for i in range(1, 65):
                entry_ptr = client_base + dwEntityList + (i * 0x78) + 0x10
                entity_pawn = pm.read_int(entry_ptr)
                if not entity_pawn:
                    continue

                dormant = pm.read_bool(entity_pawn + m_bDormant)
                if dormant:
                    continue

                team = pm.read_int(entity_pawn + m_iTeamNum)
                if team not in (2, 3):
                    continue

                health = pm.read_int(entity_pawn + m_iHealth)
                if health <= 0 or health > 100:
                    continue

                pos = read_vector3(pm, entity_pawn + m_vOldOrigin)
                screen_pos = world_to_screen(view_matrix, pos, screen_width, screen_height)
                if screen_pos:
                    draw_overlay(screen_pos, health, team)

            time.sleep(0.005)
        except:
            # Ignore all errors silently
            pass

if __name__ == "__main__":
    main_loop()