# LED Manufacturer Research: Dial-Tunable Systems for PGM/REE Metallurgical Processing
**STARE Research Division — June 25, 2026**

## Device Identified in Reference Images

The device shown (@TheInternetJeti, June 24 2026) has a **hex rotary dial** interface:

### Wavelength Dial (0–F)
| Dial | Wavelength | Primary PGM/REE Target (from PDF §2) |
|------|-----------|---------------------------------------|
| 0    | PROG      | Programmable / custom sequence        |
| 1    | 280 nm    | Pt secondary (§2.3.1), Gd (§2.4.1)  |
| 2    | 367 nm    | Tb (§2.4.1 ~365nm), Sm, Ag photolysis |
| 3    | 405 nm    | Ag SPR (§2.2), Eu (§2.4.1), Pd (§2.3.2) |
| 4    | 448 nm    | Ru/Rh excitation (§2.3.3/2.3.6), Ho (§2.4.1) |
| 5    | 470 nm    | Nd excitation adjacent (464nm §2.4.1) |
| 6    | 505 nm    | Tb emission verification (§3.5 Ch14 ~490nm) |
| 7    | 530 nm    | Au SPR primary (§2.1, ~520nm) ✓ CLOSEST |
| 8    | 568 nm    | Tb emission verify (§2.4.1 ~546nm)   |
| 9    | 591 nm    | Eu emission verify (§2.4.1 ~594nm)   |
| A    | 617 nm    | Eu emission verify (§2.4.1 ~617nm) ✓ EXACT |
| B    | 627 nm    | Eu/Pr range                           |
| C    | 655 nm    | Er excitation (§2.4.1 ~660nm) ✓ CLOSE |
| D    | 740 nm    | NIR (§3.5 Ch22 730nm)                |
| E    | 850 nm    | NIR broad (§3.5 Ch25 850nm) ✓ EXACT  |
| F    | 940 nm    | NIR (§3.5 Ch26 ~940nm) ✓ CLOSE       |

### Power Dial (0–F): 0=OFF, 1=100mW through F=1.5W (100mW steps)

**Gap vs. PDF's 32-channel map:** This device misses deep UV (254–265nm for Pt/Os/Ir primary lines). Must supplement with SETi/Crystal IS AlGaN UV-C for those PGMs.

---

## Closest Manufacturer Match to This Device

### 1. PRIZMATIX — Israel (prizmatix.com) — **BEST MATCH**
The hex-dial form factor, I2C microcontroller interface, and discrete wavelength channel layout in the video most closely matches Prizmatix architecture.

- **CombiLED**: Up to 8 combined wavelengths, single fiber output, hex-addressable channels
- **UHP-F-LED**: Individual wavelength modules (280–1100nm) that snap into combiner
- **Control**: I2C direct from ESP32/STM32 — same as shown device
- **Power range**: 0–2000mW per channel (covers the 100mW–1.5W dial range shown)
- **Matching wavelengths available**: 280, 365, 405, 450, 470, 530, 590, 617, 660, 740, 850, 940nm — almost 1:1 with dial positions 1–F
- **Why it fits**: The discrete LED + combiner architecture produces the exact fixed-wavelength discrete channel list (not continuously variable) that matches the dial positions shown

### 2. MIGHTEX SYSTEMS — Canada (mightexsystems.com) — **CLOSE SECOND**
- **WFC-BLS series**: Multi-wavelength fiber-coupled, up to 8 LEDs combined
- Same I2C/USB control architecture
- Wavelengths 280–1100nm available
- Slightly fewer catalog wavelength options than Prizmatix but same concept

### 3. THORLABS — USA (thorlabs.com) — **DIY equivalent**
- Multiple LEDD1B drivers (1.2A each) on a shared controller
- M280LP1 (280nm), M365LP1 (365nm), M405L4 (405nm), M450LP1 (450nm), M530L4 (530nm), M617L3 (617nm), M660L4 (660nm), M850L3 (850nm) — covers most dial positions
- The device in the video may BE a Thorlabs multi-LED assembly in a custom controller enclosure

### 4. GAMMA SCIENTIFIC SpectralLED RS-7-VIS — USA (gamma-sci.com) — **HIGH-END**
- 32 LED channels, 16-bit DAC control
- Covers 380–1000nm (misses 280nm)
- More channels than shown device but same discrete-wavelength philosophy
- The "dial" equivalent is software/SCPI control

---

## Wavelength Gap Analysis for Full PGM/REE Coverage

### What the dial device (280–940nm) COVERS well:
| Metal | Target λ | Dial Position | Match Quality |
|-------|----------|---------------|---------------|
| Au (SPR) | 520nm | Ch7 (530nm) | ±10nm — good for photoreduction |
| Ag (SPR) | 405–420nm | Ch3 (405nm) | Exact |
| Eu³⁺ excitation | 394nm | Ch3 (405nm) | ±11nm — acceptable |
| Eu³⁺ emission verify | 617nm | ChA (617nm) | Exact |
| Tb³⁺ excitation | 365nm | Ch2 (367nm) | ±2nm — excellent |
| Pd (porphyrin) | 405–415nm | Ch3 (405nm) | Exact |
| Ru(bpy)₃²⁺ | 450–460nm | Ch4 (448nm) | ±2nm — excellent |
| Ho³⁺ excitation | 450–460nm | Ch4 (448nm) | ±2nm — excellent |
| Er³⁺ excitation | 660nm | ChC (655nm) | ±5nm — good |
| Nd³⁺ excitation | 808nm | NOT PRESENT | Gap |
| Yb³⁺ excitation | 980nm | NOT PRESENT | Gap |

### What the dial device MISSES (requires supplement):
| Metal | Target λ | Required Supplement Source |
|-------|----------|---------------------------|
| Pt (primary) | 265nm | SETi UVTOP265 / Crystal IS |
| Pt (secondary) | 254nm | SETi UVTOP254 |
| Os (primary) | 225–263nm | SETi / Seoul Viosys Violeds |
| Ir (primary) | 224–254nm | SETi UVTOP255 |
| Rh (primary) | 343nm | UV-A LED ~340nm (Nichia/OSA) |
| Nd (NIR pump) | 808nm | Thorlabs L808P500MM or Roithner ELJ-808 |
| Yb/Er (NIR) | 980nm | Roithner / Thorlabs L980P100 |

---

## Resonant Frequency Fine-Tuning Recommendations

### For Gold (Au) — Dial position 7 (530nm)
- PDF target: 520nm (SPR peak)
- Dial gives 530nm — **+10nm offset**
- Compensate: increase irradiance (higher dial power setting) — photoreduction still efficient at 530nm
- If SPR peak needs to be exact: **Ossila Tunable Light Source** (sub-nm accuracy, 380–1000nm) allows sweeping to find your specific particle batch's SPR maximum

### For Silver (Ag) — Dial position 3 (405nm)
- PDF target: 400–420nm (SPR), 365nm (photoreduction)
- Dial position 3 (405nm) is optimal for both SPR and photoreduction simultaneously
- Dual-dial approach: run Ch2 (367nm) and Ch3 (405nm) simultaneously if combiner supports it

### For Rhodium (Rh) — Dial position 2 (367nm)
- PDF target: 343–370nm band
- 367nm falls within the photocatalytic recovery window — use maximum power (F = 1.5W)

### For Europium (Eu³⁺) — Dial position 3 (405nm) → verify with A (617nm)
- Excite at Ch3 (405nm), monitor emission at ChA (617nm)
- The dial device can do excitation + emission verification in sequence

### For Terbium (Tb³⁺) — Dial position 2 (367nm)
- Exact match for Tb³⁺ canonical 365nm excitation
- Monitor emission at Ch7/Ch8 (530/568nm) for 546nm dominant green line

---

## Priority Purchase Path (to complement the dial device)

| Gap | Solution | Manufacturer | Est. Cost |
|-----|----------|-------------|-----------|
| 254–265nm for Pt/Os/Ir | UVTOP265 AlGaN LED + driver | SETi / crystal-is.com | $200–500/unit |
| 340–343nm for Rh precise | NSPU519B 340nm | Nichia via Mouser | $50–150 |
| 808nm for Nd pump | L808P500MM pigtailed | Thorlabs | $400–800 |
| 980nm for Yb/Er | L980P100 | Thorlabs | $300–600 |
| Sub-nm tuning sweep | Ossila Tunable Light Source | ossila.com | $2,000–5,000 |

---

## Closest Single-Device Match for Full PGM/REE Coverage

**Prizmatix CombiLED** configured with these 8 modules:
1. UHP-F-280 (280nm) — Pt, Gd
2. UHP-F-365 (365nm) — Tb, Sm, Ag  
3. UHP-F-405 (405nm) — Ag SPR, Eu, Pd
4. UHP-F-450 (450nm) — Ru, Ho, Os
5. UHP-F-530 (530nm) — Au SPR
6. UHP-F-617 (617nm) — Eu emission
7. UHP-F-660 (660nm) — Er excitation
8. UHP-F-850 (850nm) — NIR broad

This 8-channel Prizmatix CombiLED mirrors the dial device almost exactly, with I2C microcontroller control, fiber output to reaction vessel, and 12-bit power resolution per channel — far finer than the 16-step (100mW) dial shown in the video.

**Contact**: prizmatix.com — sales@prizmatix.com

---

*Cross-referenced against: STARE Research Division PDF "High-Capacity LED Systems for Metallurgical Photonic Processing" June 25, 2026*
