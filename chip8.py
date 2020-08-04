"""
Chip8 Emulator

By Dean Lawrence
"""

import pygame
import argparse
import time
import random

class Chip8Emulator():
    def __init__(self, rate=400):
        
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 512, 256
        self.period = 1 / rate

        self._mem = [0 for i in range(0, 4096)]
        self._vmem = [1 for i in range(0, 64 * 32)]

        self._pc = 512
        self._I = 0
        self._stack = []

        self._delay_timer = 0
        self._sound_timer = 0

        self._timer_accrual = 0
        self._timer_period = 1 / 60

        self._regs = [0 for i in range(0, 16)]

        self._font = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,   # 0
            0x20, 0x60, 0x20, 0x20, 0x70,   # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,   # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,   # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,   # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,   # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,   # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,   # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,   # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,   # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,   # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,   # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,   # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,   # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,   # E
            0xF0, 0x80, 0xF0, 0x80, 0x80    # F
        ]

        self.copy_font_into_memory()

        self._key_map = {
            '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
            'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
        }
    
    def init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption('Chip8 Emulator')
        self._running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        
    def loop(self):
        
        # Fetch
        hb = self._mem[self._pc]
        lb = self._mem[self._pc + 1]
        self._pc += 2

        # Decode and Execute I guess
        # Instruction has four nibbles, ir | X | Y | N
        ir = (hb & 0b11110000) >> 4
        X = (hb & 0b00001111)
        Y = (lb & 0b11110000) >> 4
        N = (lb & 0b00001111)
        NN = lb
        NNN = (X << 8) + lb

        if ir == 0x0:      # Done
            if NN == 0xE0:
                self._vmem = [0 for i in range(0, 64 * 32)]
            elif NN == 0xEE:
                self._pc = self._stack.pop()
        elif ir == 0x1:    # Done
            self._pc = NNN
        elif ir == 0x2:    # Done
            self._stack.append(self._pc)
            self._pc = NNN
        elif ir == 0x3:    # Done
            if self._regs[X] == NN:
                self._pc += 2
        elif ir == 0x4:    # Done
            if self._regs[X] != NN:
                self._pc += 2
        elif ir == 0x5:    # Done
            if self._regs[X] == self._regs[Y]:
                self._pc += 2
        elif ir == 0x6:    # Done
            self._regs[X] = NN
        elif ir == 0x7:    # Done
            self._regs[X] += NN
            self._regs[X] %= 256
        elif ir == 0x8:    # Done
            if N == 0x0:
                self._regs[X] = self._regs[Y]
            elif N == 0x1:
                self._regs[X] |= self._regs[Y]
            elif N == 0x2:
                self._regs[X] &= self._regs[Y]
            elif N == 0x3:
                self._regs[X] ^= self._regs[Y]
            elif N == 0x4:
                self._regs[X] += self._regs[Y]

                if self._regs[X] > 0xFF:
                    self._regs[0xF] = 1
                    self._regs[X] %= 256
                else:
                    self._regs[0xF] = 0
                
            elif N == 0x5:
                if self._regs[X] > self._regs[Y]:
                    self._regs[0xF] = 1
                else:
                    self._regs[0xF] = 0

                self._regs[X] = (self._regs[X] - self._regs[Y]) % 256
            elif N == 0x6:
                self._regs[0xF] = (self._regs[X] & 0b10000000) >> 7

                self._regs[X] = self._regs[X] << 1
            elif N == 0x7:
                if self._regs[Y] > self._regs[X]:
                    self._regs[0xF] = 1
                else:
                    self._regs[0xF] = 0
                    
                self._regs[X] = (self._regs[Y] - self._regs[X]) % 256
            elif N == 0xE:
                self._regs[0xF] = (self._regs[X] & 0b00000001)
                
                self._regs[X] = self._regs[X] >> 1
        elif ir == 0x9:    # Done
            if self._regs[X] != self._regs[Y]:
                self._pc += 2
        elif ir == 0xA:    # Done
            self._I = NNN
        elif ir == 0xB:    # Done
            self._pc = self._regs[0] + NNN
        elif ir == 0xC:    # Done
            self._regs[X] = random.randint(0, 255) & NN
        elif ir == 0xD:     # Done
            
            x_pos = self._regs[X] % 64
            y_pos = self._regs[Y] % 32
            self._regs[0xF] = 0

            for i in range(N):
                sprite_row = self._mem[self._I + i]
                for j in range(8):
                    bit_addr = 8 - j
                    bit = (sprite_row & (1 << bit_addr)) >> bit_addr

                    current_val = self._vmem[x_pos * 32 + y_pos]

                    if current_val == 1 and bit == 1:
                        self._vmem[x_pos * 32 + y_pos] = 0
                        self._regs[0xF] = 1
                    elif bit == 1 and current_val == 0:
                        self._vmem[x_pos * 32 + y_pos] = 1

                    x_pos += 1

                    if x_pos >= 64:
                        break
                
                x_pos = self._regs[X] % 64
                y_pos += 1

                if y_pos >= 32:
                    break

        elif ir == 0xE: # Skip if key
            pass
        elif ir == 0xF:
            if NN == 0x07:
                self._regs[X] = self._delay_timer

            elif NN == 0x15:
                self._delay_timer = self._regs[X]

            elif NN == 0x18:
                self._sound_timer = self._regs[X]

            elif NN == 0x1E:
                self._I += self._regs[X]

                if self._I >= 0x1000:
                    self._I %= 0x1000
                    self._regs[0xF] = 1
                
            elif NN == 0x0A:
                """
                for event in pygame.event.get():
                    if event.type == pygame.
                    self._regs[X] = self._key_map[]
                """
            elif NN == 0x29:
                self._I = (self._regs[X] & 0x0F) * 5

            elif NN == 0x33:
                num = self._regs[X]
                self._mem[self._I + 2] = num % 10
                num //= 10
                self._mem[self._I + 1] = num % 10
                num //= 10
                self._mem[self._I] = num % 10

            elif NN == 0x55:
                for i in range(X + 1):
                    self._mem[self._I + i] = self._regs[i]
                
            elif NN == 0x65:
                for i in range(X + 1):
                    self._regs[i] = self._mem[self._I + i]


    def render(self):
        
        for i in range(64):
            for j in range(32):
                if self._vmem[i * 32 + j] == 1:
                    pygame.draw.rect(self._display_surf, (255, 255, 255), pygame.Rect(i * 8, j * 8, 8, 8))
                else:
                    pygame.draw.rect(self._display_surf, (0, 0, 0), pygame.Rect(i * 8, j * 8, 8, 8))
        
        pygame.display.update()
    
    def cleanup(self):
        pygame.quit()

    def read_rom_into_memory(self, path):

        address = 512
        with open(path, 'rb') as fp:
            while True:
                byte = fp.read(1)
                
                if not byte:
                    break

                self._mem[address] = byte[0]
                address += 1

        return 1
    
    def copy_font_into_memory(self, starting_location=0):
        for i, byte in enumerate(self._font):
            self._mem[starting_location + i] = byte
    
    def execute(self):
        if self.init() == False:
            self._running = False
        
        while self._running:
            
            start_time = time.time()
            
            for event in pygame.event.get():
                self.on_event(event)
            
            self.loop()
            self.render()

            delta = time.time() - start_time
            if delta < self.period:
                time.sleep(self.period - delta)

            self._timer_accrual += delta
            if self._timer_accrual > self._timer_period:
                self.timer_accrual = 0
                if self._delay_timer > 0:
                    self._delay_timer -= 1
                
                if self._sound_timer > 0:
                    self._sound_timer -= 1
            
        
        self.cleanup()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("rom_path", type=str, help="Path to rom file")

    args = parser.parse_args()

    emu = Chip8Emulator()
    emu.read_rom_into_memory(args.rom_path)
    emu.execute()

if __name__ == "__main__":
    main()
