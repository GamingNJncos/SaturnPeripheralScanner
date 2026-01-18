# SaturnPeripheralScanner
A Peripheral Support Scanner for Sega Saturn


Goal:
To aid in testing edge cases for [BLE-3D](https://github.com/GamingNJncos/BLE-3D-Saturn-Public) and even more so morbid curiosity as to what's actually enabled in ISO/BIN's vs what was advertised at launch I sl(a/o)pped this together. I have a sneaking suspicion a few games are floating around with extra Peripheral support beyond what was advertised, and beta builds/unreleased, specific region games with things purposely or not left enabled.  The saturn has a bunch of various Peripherals and I wasn't aware of a similar tool to do this so here we are. I'm lazy, so doing this per bin/iso wasn't reasonable so script seemed like a good option.

Warning - This is my initial pass at this and could be completely broken/non functional atm. 

Use:
./python3 GNJ_SaturnPeripheralScanner.py ./
Toss the .py file (tested on python3) in a directory with saturn games or manually specify the path

How does it work? 
Per this Disc format specifications sheet what I was interested in should be around 50H/0x50  [ST-040-R4-051795.pdf](https://segaretro.org/images/b/be/ST-040-R4-051795.pdf)
<img width="1256" height="838" alt="image" src="https://github.com/user-attachments/assets/414881cf-9640-4d3a-89ee-c3d168494746" />

Note: If you have done any saturn region patching (also commonly pointed to 0x50 in discussion) before this is right after it. It's actually at 0x60 in most images/bin (but there are things that can impact that. Here look at it, See. The location changes from 50H but the data we're after is the same, right by the region details 
<img width="1130" height="364" alt="image" src="https://github.com/user-attachments/assets/9b0d2fd2-ae33-436f-ae2b-e8fd8286c86a" />


Here's the table from the doc linked above 
** Peripheral Code Reference:**
```
A = Analog Controller (Mission Stick)
   C = Link Cable (Japan)
   D = DirectLink Cable (USA)
   E = Analog Controller (3D Multi-Controller)
   F = Floppy Disk Drive
   G = Gun (Virtua Gun)
   J = Control Pad (Standard Joypad)
   K = Keyboard
   M = Mouse
   P = Video CD Card (MPEG)
   Q = Pachinko Controller
   R = ROM Cartridge (Required)
   S = Steering Controller (Arcade Racer)
   T = Multitap
   W = RAM Cartridge (1MB/4MB)
   X = X-Band/Netlink Modem
```

**Example output:**
```
cat GNJ_SaturnPeripheralScanner.txt

# GNJ Saturn Peripheral Scanner v2.0.0
# Author: GNJ Tools
# Generated: 2026-01-18 16:14:34
# Total files scanned: 127
#
# Peripheral Code Reference:
#   A = Analog Controller
#   C = Link Cable (JP)
#   D = DirectLink (US)
#   E = 3D Controller
#   F = Floppy Drive
#   G = Virtua Gun
#   J = Control Pad
#   K = Keyboard
#   M = Mouse
#   P = Video CD Card
#   Q = Pachinko Controller
#   R = ROM Cartridge
#   S = Steering Controller
#   T = Multitap
#   W = RAM Cartridge
#   X = NetLink Modem
#
# Format: Game_Title (0x60) | Version (0x2A) | Peripheral_Codes (0x50) | Supported Peripheral | Source Filename
#===================================================================================================================================================================================

Game_Title (0x60)                                  | Version  | Peripheral_Codes   | Supported Peripherals                                   | Source Filename
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
STREET FIGHTER COLLECTION                          | V1.000   | J                  | Control Pad                                             | Street Fighter Collection.iso
VF. KIDS                                           | V0.001   | J                  | Control Pad                                             | Track No01.iso
SEGA TOURING CARCHAMPIONSHIP                       | V1.003   | EJS                | 3D Controller, Control Pad, Steering Controller         | 01.iso
STREET FIGHTER ZERO3                               | V1.002   | JW                 | Control Pad, RAM Cartridge                              | Street Fighter Zero 3.iso
Shining Wisdom                                     | V1.000   | J                  | Control Pad                                             | Shining Wisdom.bin
BOMBERMAN WARS                                     | V1.000   | J                  | Control Pad                                             | Bomberman Wars.iso
DIE HARD ARCADE                                    | V1.002   | J                  | Control Pad                                             | Track No01.iso
DAYTONA USA C.C.E. NET LINK EDITION                | V1.000   | JSEDX              | Control Pad, Steering Controller, 3D Controller, Dir... | DAYTONA_REMIX.bin
METAL SLUG                                         | V1.002   | JW                 | Control Pad, RAM Cartridge                              | Metal Slug.iso
LAYER SECTION                                      | V1.002   | J                  | Control Pad                                             | Layer Section.iso
ELEVATOR ACTION RETURNS                            | V1.002   | J                  | Control Pad                                             | Elevator Action² Returns.bin
SEGA RALLY CHAMPIONSHIP                            | V1.000   | JAS                | Control Pad, Analog Controller, Steering Controller     | Sega Rally.iso
DARK SEED 2                                        | V1.004   | J                  | Control Pad                                             | DW-617-Sat-Dark_Seed_II(J).bin
MARVEL SUPER HEROES VS. STREET FIGHTER             | V1.000   | JW                 | Control Pad, RAM Cartridge                              | s-MvSF.bin
```



