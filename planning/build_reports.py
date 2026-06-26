"""
STARE Research Division — PDF Report Builder
Light background, dark text, high contrast (WCAG AA).

ARCHITECTURE NOTE:
  Use PageTemplate(onPage=...) for background/chrome — it fires BEFORE content
  is placed on each page, so nothing gets painted over.
  Never use a custom Canvas subclass that replays pages after the fact.
"""

from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                 Paragraph, Spacer, Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

W, H = letter

# ── Palette (WCAG AA on white) ────────────────────────────────────────────────
BG       = colors.white
TEXT     = colors.HexColor('#111111')
ACCENT   = colors.HexColor('#00695C')   # deep teal
ACCENT2  = colors.HexColor('#1565C0')   # deep blue
LINK     = colors.HexColor('#0D47A1')
ROW_ALT  = colors.HexColor('#F0F4F8')
HDR_BG   = colors.HexColor('#E0F2F1')
RULE     = colors.HexColor('#90CAF9')
HDR_BAR  = colors.HexColor('#004D40')   # very dark teal
FTR_BAR  = colors.HexColor('#004D40')

# ── Paragraph styles ──────────────────────────────────────────────────────────
h1     = ParagraphStyle('h1',   fontName='Helvetica-Bold',    fontSize=16,
                                textColor=ACCENT,  spaceAfter=6,  leading=20)
h2     = ParagraphStyle('h2',   fontName='Helvetica-Bold',    fontSize=12,
                                textColor=ACCENT,  spaceAfter=4,  leading=16)
h3     = ParagraphStyle('h3',   fontName='Helvetica-Bold',    fontSize=10,
                                textColor=ACCENT2, spaceAfter=3,  leading=13)
body   = ParagraphStyle('body', fontName='Helvetica',         fontSize=9,
                                textColor=TEXT,    spaceAfter=4,  leading=13)
url_s  = ParagraphStyle('url',  fontName='Helvetica',         fontSize=9,
                                textColor=LINK,    spaceAfter=4,  leading=13)
small  = ParagraphStyle('sm',   fontName='Helvetica',         fontSize=8,
                                textColor=colors.HexColor('#333333'), leading=11)

def lnk(txt, url):
    return f'<link href="{url}" color="#0D47A1"><u>{txt}</u></link>'

# ── Table style ───────────────────────────────────────────────────────────────
BASE_TBL = TableStyle([
    ('BACKGROUND',    (0, 0), (-1,  0), HDR_BG),
    ('TEXTCOLOR',     (0, 0), (-1,  0), HDR_BAR),
    ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
    ('FONTSIZE',      (0, 0), (-1,  0), 9),
    ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE',      (0, 1), (-1, -1), 8),
    ('TEXTCOLOR',     (0, 1), (-1, -1), TEXT),
    ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BG, ROW_ALT]),
    ('GRID',          (0, 0), (-1, -1), 0.4, RULE),
    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING',    (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING',   (0, 0), (-1, -1), 5),
])

# ── Page chrome (onPage callback — fires BEFORE content) ─────────────────────
def make_page_fn(report_title, total_pages_ref):
    def draw_chrome(canvas, doc):
        canvas.saveState()
        # 1. White background — must be first
        canvas.setFillColor(BG)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # 2. Header bar
        canvas.setFillColor(HDR_BAR)
        canvas.rect(0, H - 36, W, 36, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(0.5 * inch, H - 22, report_title)
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(W - 0.5 * inch, H - 22, 'STARE Research Division — June 2026')
        # 3. Footer bar
        canvas.setFillColor(HDR_BAR)
        canvas.rect(0, 0, W, 22, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(0.5 * inch, 7, 'Confidential — Internal Research Use Only')
        canvas.drawRightString(W - 0.5 * inch, 7, f'Page {doc.page}')
        canvas.restoreState()
    return draw_chrome


def make_doc(path, title):
    doc = BaseDocTemplate(
        path, pagesize=letter,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=0.65 * inch,  bottomMargin=0.45 * inch,
    )
    page_fn = make_page_fn(title, None)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=page_fn)])
    return doc


def even_cols(doc, n):
    return [doc.width / n] * n


# ─────────────────────────────────────────────────────────────────────────────
# REPORT 1 — Gas Discharge Arc Lamp Manufacturers
# ─────────────────────────────────────────────────────────────────────────────

def build_gas_discharge_pdf():
    OUT   = '/home/user/Wintermute/planning/GasDischarge-Manufacturer-Reference.pdf'
    TITLE = 'Gas Discharge Arc Lamp Manufacturers — 528 nm SPR / PGM-REE Processing'
    doc   = make_doc(OUT, TITLE)
    S     = []

    S.append(Paragraph(TITLE, h1))
    S.append(Paragraph(
        'Specification: Dielectric breakdown gas discharge apparatus — gaseous medium in dielectric '
        'housing sustaining electrical arc discharge — primary emission 528 nm (green) for Au/Ag SPR '
        'excitation in comminuted ore processing — continuous or pulsed UV-Vis-NIR output across '
        'PGM and REE absorption bands.',
        body))
    S.append(HRFlowable(width='100%', thickness=1, color=RULE, spaceAfter=8))

    S.append(Paragraph('Technology Overview', h2))
    tech = [
        ['Technology',        'Gas Medium',    'Housing',           '528 nm?',       'UV',        'NIR'],
        ['Xe Short Arc',      'Xenon',         'Quartz (SiO₂)',     'Continuum ✓',   '< 200 nm',  '2500 nm'],
        ['Hg-Xe Arc',         'Hg + Xe',       'Quartz',            '+ 546nm line',  '185 nm+',   '2500 nm'],
        ['Kr Arc',            'Krypton',       'Quartz',            'Continuum ✓',   '< 200 nm',  '1000 nm'],
        ['LDLS (laser Xe)',   'Xenon',         'Quartz dielectric', 'Continuum ✓',   '170 nm',    '2100 nm'],
        ['CERMAX',            'Xenon',         'Al₂O₃ ceramic',     'Continuum ✓',   '< 250 nm',  '1000 nm'],
        ['DBD excimer',       'Xe/Kr/Hg',      'Dielectric glass',  'Narrow UV only','VUV',       'limited'],
        ['Microwave plasma',  'Sulfur vapor',  'Quartz',            '~520 nm ★',     'visible',   'limited'],
    ]
    S.append(Table(tech, colWidths=[1.05*inch]*6, style=BASE_TBL))
    S.append(Spacer(1, 10))

    mfrs = [
        {
            'rank': '★★★★★  BEST MATCH',
            'name': 'Energetiq Technology (Hamamatsu group)',
            'product': 'LDLS EQ-99XFC / EQ-77',
            'url': 'https://www.energetiq.com/ldls-laser-driven-light-source',
            'desc': (
                'Laser-Driven Light Source: a CW laser sustains a Xe plasma inside a sealed fused-quartz '
                'dielectric bulb — electrodeless, no electrode erosion. Delivers 170–2100 nm continuous '
                'output covering every PGM and REE absorption band. ~10× higher radiance than conventional '
                'Xe arcs. Fiber-coupled output direct to reaction vessel.'
            ),
            'specs': [
                ['Parameter',      'EQ-99XFC',              'EQ-77'],
                ['Spectral range',  '170–2100 nm',           '200–1100 nm'],
                ['Radiance',        '> 1 mW/nm @ 400 nm',   '> 0.5 mW/nm'],
                ['Stability',       '< 0.2% RMS',           '< 0.5% RMS'],
                ['Housing',         'Fused silica (SiO₂)',  'Fused silica'],
                ['Discharge type',  'Laser-sustained Xe plasma', 'Laser-sustained'],
                ['Arc spot size',   '< 100 µm',             '< 100 µm'],
                ['Output',          'SMA-905 fiber',         'SMA-905 fiber'],
            ],
        },
        {
            'rank': '★★★★★  LITERAL SPEC MATCH',
            'name': 'Excelitas Technologies — CERMAX',
            'product': 'PE300BF / PE150BF / PE75BF',
            'url': 'https://www.excelitas.com/product-category/cermax-xenon-arc-lamps',
            'desc': (
                'CERMAX = Ceramic Maximum. The Al₂O₃ ceramic reflector IS the dielectric housing — '
                'Xe arc burns inside a parabolic ceramic cavity producing collimated UV-Vis-NIR output. '
                'Long life (1000+ hrs), cold-restrike capable. Available 75 W–1600 W.'
            ),
            'specs': [
                ['Model',    'Power',   'Life',    'Range',       'Color temp'],
                ['PE75BF',   '75 W',    '500 hr',  '240–2500 nm', '5500 K'],
                ['PE150BF',  '150 W',   '1000 hr', '240–2500 nm', '5800 K'],
                ['PE300BF',  '300 W',   '1000 hr', '240–2500 nm', '6000 K'],
                ['PE1000',   '1000 W',  '500 hr',  '230–2500 nm', '6200 K'],
            ],
        },
        {
            'rank': '★★★★  CLOSEST 528 nm NATURAL PEAK',
            'name': 'Topanga Technologies / Luxim — Sulfur Plasma',
            'product': 'LiFi Sulfur Plasma Lamp',
            'url': 'https://www.topangatech.com',
            'desc': (
                'Sulfur vapor microwave plasma in quartz dielectric bulb. Natural emission peak ~520 nm '
                '— closest of any discharge lamp to 528 nm SPR target without bandpass filtering. '
                '430–750 nm visible band, electrodeless, 50,000+ hr life.'
            ),
            'specs': [
                ['Parameter',      'Value'],
                ['Peak emission',   '~520 nm (natural)'],
                ['Spectral range',  '430–750 nm'],
                ['Drive',           '2.45 GHz microwave'],
                ['Housing',         'Fused quartz dielectric bulb'],
                ['Lifetime',        '50,000+ hours'],
                ['Input power',     '1000–1400 W'],
            ],
        },
        {
            'rank': '★★★★',
            'name': 'Newport / MKS Instruments — Oriel Series',
            'product': 'Model 66902 / 69911 Xe Arc',
            'url': 'https://www.newport.com/c/arc-lamp-sources',
            'desc': (
                'Industry-standard Xe short arc systems, quartz envelope, 150 W–1000 W, '
                '200–2500 nm continuum. The 66902 (150 W) is a workhorse for photocatalysis research.'
            ),
            'specs': [
                ['Model',       'Power',  'Range',       'Notes'],
                ['66902',       '150 W',  '200–2500 nm', 'Photocatalysis / SPR standard'],
                ['69911',       '300 W',  '200–2500 nm', 'High irradiance'],
                ['Hg-Xe 66142', '200 W',  '185–2500 nm', 'UV-enhanced + 546 nm line'],
            ],
        },
        {
            'rank': '★★★★',
            'name': 'Hamamatsu Photonics',
            'product': 'L10671 / L9455 Flash Xe',
            'url': 'https://www.hamamatsu.com/us/en/product/light-sources/xenon-flash-lamps.html',
            'desc': (
                'Xe short arc lamps (CW and flash) plus fiber-coupled output. L9455 flash series '
                'provides pulsed µs pulses for time-resolved PGM/REE luminescence.'
            ),
            'specs': [
                ['Model',   'Type',     'Range',       'Power'],
                ['L10671',  'CW Xe',    '200–2000 nm', '150 W'],
                ['L11035',  'CW Xe',    '200–2000 nm', '75 W compact'],
                ['L9455',   'Flash Xe', '200–1000 nm', 'pulsed < 10 ms'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'ams OSRAM — XBO Series',
            'product': 'XBO 75W / 150W / 300W',
            'url': 'https://www.ams-osram.com/products/lamps/xenon-short-arc-lamps',
            'desc': (
                'Ultra-high pressure Xe short arc, sub-mm arc gap, extremely high luminance. '
                'UV-transmitting quartz, output to 230 nm — covers Pt (265 nm), Os, Ir primary lines.'
            ),
            'specs': [
                ['Model',          'Power',   'Arc gap', 'Color temp'],
                ['XBO 75W/2',      '75 W',    '0.8 mm',  '6200 K'],
                ['XBO 150W/4',     '150 W',   '1.2 mm',  '6200 K'],
                ['XBO 300W/4',     '300 W',   '2.0 mm',  '6000 K'],
                ['XBO 1000W/HS',   '1000 W',  '5.5 mm',  '6100 K'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Ushio America',
            'product': 'UXL / SX Series',
            'url': 'https://www.ushio.com/products/arc-lamps/',
            'desc': 'Xe short arc and Hg-Xe, 230–2500 nm, ceramic holders for harsh environments.',
            'specs': [
                ['Model',      'Power',  'Range'],
                ['UXL-75XE',   '75 W',   '230–2500 nm'],
                ['UXL-300D',   '300 W',  '230–2500 nm'],
                ['UXL-500D',   '500 W',  '230–2500 nm'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Resonance Ltd — Canada',
            'product': 'Microwave Electrodeless Lamps',
            'url': 'https://www.resonance.on.ca',
            'desc': (
                'Electrodeless microwave-excited discharge lamps, gas-fill selectable (Xe, Kr, Hg, Ar). '
                'Quartz dielectric bulb, 2.45 GHz driver, pulsed or CW. Widely used in analytical spectroscopy.'
            ),
            'specs': [
                ['Fill gas', 'Key emission lines'],
                ['Xenon',   '823, 828, 881 nm + continuum'],
                ['Mercury', '185, 254, 365, 405, 436, 546, 578 nm'],
                ['Krypton', '758, 760, 769, 811 nm'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Edinburgh Instruments',
            'product': 'Xe900 / µF920H Xe Flashlamp',
            'url': 'https://www.edinst.com/products/light-sources/',
            'desc': (
                'Pulsed Xe flashlamps (< 1 µs pulses) for time-resolved luminescence of Eu³⁺, Tb³⁺, '
                'Nd³⁺ during REE separation monitoring. 200–900 nm, quartz housing.'
            ),
            'specs': [
                ['Model',   'Type',     'Pulse',   'Range'],
                ['Xe900',   'CW Xe',    'CW',      '200–900 nm'],
                ['µF920H',  'Flash Xe', '< 1 µs',  '200–900 nm'],
            ],
        },
        {
            'rank': '★★',
            'name': 'Heraeus Noblelight',
            'product': 'DBD Excimer / Xe Flash Lamps',
            'url': 'https://www.heraeus.com/en/hng/products_and_solutions/uv_curing/xenon_flash_lamps.html',
            'desc': (
                'True dielectric barrier discharge (DBD) excimer lamps: 172 nm Xe₂*, 222 nm KrCl*, '
                '308 nm XeCl* — narrow UV bands for Pt/Os/Ir primary lines. Also broad-spectrum Xe flash.'
            ),
            'specs': [
                ['Type',            'Wavelength', 'PGM application'],
                ['Xe₂* excimer',    '172 nm',     'Os/Ir VUV photolysis'],
                ['KrCl* excimer',   '222 nm',     'Ir primary line region'],
                ['XeCl* excimer',   '308 nm',     'Rh photocatalysis'],
                ['Xe flash',        '200–2500 nm','Broad-spectrum photocatalysis'],
            ],
        },
    ]

    for m in mfrs:
        S.append(Spacer(1, 6))
        S.append(Paragraph(f"{m['rank']} — {m['name']}", h2))
        S.append(Paragraph(f"Product: {m['product']}", h3))
        S.append(Paragraph(m['desc'], body))
        S.append(Paragraph(lnk(f"Website: {m['url']}", m['url']), url_s))
        if 'specs' in m:
            nc = len(m['specs'][0])
            S.append(Table(m['specs'], colWidths=even_cols(doc, nc), style=BASE_TBL))
        S.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceAfter=4))

    S.append(Spacer(1, 8))
    S.append(Paragraph('Spectral Coverage Matrix vs PGM/REE Targets', h2))
    matrix = [
        ['Target',   'λ (nm)',   'Energetiq LDLS', 'CERMAX Xe', 'Sulfur Plasma', 'Hg-Xe',   'DBD'],
        ['Au SPR',   '520–528',  '✓ continuum',    '✓',         '★ peak ~520',   '✓',        '—'],
        ['Ag SPR',   '400–420',  '✓',              '✓',         '—',             '✓ 405nm',  '—'],
        ['Pd',       '340 nm',   '✓',              '✓',         '—',             '✓',        'XeCl~308'],
        ['Rh',       '343 nm',   '✓',              '✓',         '—',             '✓',        'XeCl~308'],
        ['Pt',       '265 nm',   '✓',              '✓',         '—',             '✓',        'KrCl~222'],
        ['Os/Ir',    '224–226',  '✓',              '✓',         '—',             '✓',        'Xe₂*172'],
        ['Eu³⁺',    '394 nm',   '✓',              '✓',         '—',             '✓ 405nm',  '—'],
        ['Tb³⁺',    '365 nm',   '✓',              '✓',         '—',             '✓ 365nm',  '—'],
        ['Er³⁺',    '660 nm',   '✓',              '✓',         '✓',             '✓',        '—'],
        ['Nd³⁺',    '808 nm',   '✓',              '✓',         '—',             '✓',        '—'],
        ['Yb³⁺',    '980 nm',   '✓',              '✓',         '—',             '✓',        '—'],
    ]
    cw = [0.6*inch, 0.65*inch, 1.05*inch, 0.85*inch, 1.0*inch, 0.7*inch, 0.75*inch]
    S.append(Table(matrix, colWidths=cw, style=BASE_TBL))

    S.append(Spacer(1, 8))
    S.append(Paragraph('Priority Purchase Path', h2))
    purchase = [
        ['Goal',                    'Product',        'Manufacturer', 'URL',                                                                         'Est. Cost'],
        ['Best UV-Vis-NIR coverage','EQ-99XFC LDLS',  'Energetiq',    lnk('energetiq.com','https://www.energetiq.com'),                             '$15k–25k'],
        ['Closest 528 nm natural',  'Sulfur lamp',    'Topanga',      lnk('topangatech.com','https://www.topangatech.com'),                          '$3k–8k'],
        ['Budget Xe + filter',      'PE150BF CERMAX', 'Excelitas',    lnk('excelitas.com','https://www.excelitas.com/product-category/cermax-xenon-arc-lamps'), '$500–2k'],
        ['Pulsed REE time-resolve', 'µF920H Flash',   'Edinburgh',    lnk('edinst.com','https://www.edinst.com/products/light-sources/'),            '$2k–5k'],
        ['Deep UV Pt/Os/Ir',        'Xe₂* 172nm DBD', 'Heraeus',      lnk('heraeus.com','https://www.heraeus.com'),                                 '$1k–3k'],
    ]
    S.append(Table(purchase,
                   colWidths=[1.3*inch, 1.0*inch, 0.85*inch, 1.45*inch, 0.7*inch],
                   style=BASE_TBL))

    S.append(Spacer(1, 10))
    S.append(Paragraph(
        'All hyperlinks active — tap/click to open. '
        'Cross-referenced: STARE Research Division PDF "High-Capacity LED Systems for '
        'Metallurgical Photonic Processing" June 25, 2026.',
        small))

    doc.build(S)
    print(f'PDF written: {OUT}')
    return OUT


# ─────────────────────────────────────────────────────────────────────────────
# REPORT 2 — LED Dial-Tuning Manufacturer Reference
# ─────────────────────────────────────────────────────────────────────────────

def build_led_pdf():
    OUT   = '/home/user/Wintermute/planning/LED-Manufacturer-Reference.pdf'
    TITLE = 'LED Dial-Tuning Manufacturers — PGM/REE Metallurgical Processing'
    doc   = make_doc(OUT, TITLE)
    S     = []

    S.append(Paragraph(TITLE, h1))
    S.append(Paragraph(
        'Hex rotary dial device (0–F wavelength × 0–F power, 100 mW steps to 1.5 W) mapped to '
        'closest commercial LED systems for Platinum Group Metal and Rare Earth Element photonic processing.',
        body))
    S.append(HRFlowable(width='100%', thickness=1, color=RULE, spaceAfter=8))

    S.append(Paragraph('Hex Dial Wavelength Decode', h2))
    dial = [
        ['Dial', 'Wavelength', 'PGM/REE Target',                  'Match Quality'],
        ['0',    'PROG',       'Custom sequence',                  '—'],
        ['1',    '280 nm',     'Pt secondary, Gd',                 'Good'],
        ['2',    '367 nm',     'Tb³⁺ (365nm), Sm, Ag photolysis', '±2 nm Excellent'],
        ['3',    '405 nm',     'Ag SPR, Eu³⁺, Pd porphyrin',      'Exact'],
        ['4',    '448 nm',     'Ru(bpy)₃²⁺, Ho³⁺',               '±2 nm Excellent'],
        ['5',    '470 nm',     'Nd adjacent (464 nm)',              '±6 nm Good'],
        ['6',    '505 nm',     'Tb emission verify',               'Good'],
        ['7',    '530 nm',     'Au SPR (peak 520 nm)',             '±10 nm Good'],
        ['8',    '568 nm',     'Tb emission (546 nm)',             '±22 nm Acceptable'],
        ['9',    '591 nm',     'Eu emission (594 nm)',             '±3 nm Excellent'],
        ['A',    '617 nm',     'Eu³⁺ emission',                   'Exact'],
        ['B',    '627 nm',     'Eu/Pr range',                     'Good'],
        ['C',    '655 nm',     'Er³⁺ excitation (660 nm)',        '±5 nm Good'],
        ['D',    '740 nm',     'NIR band',                        'Good'],
        ['E',    '850 nm',     'NIR broad',                       'Exact'],
        ['F',    '940 nm',     'NIR',                             '±40 nm Good'],
    ]
    S.append(Table(dial,
                   colWidths=[0.4*inch, 0.75*inch, 2.65*inch, 1.4*inch],
                   style=BASE_TBL))
    S.append(Spacer(1, 10))

    led_mfrs = [
        {
            'rank': '★★★★★  BEST MATCH — CombiLED mirrors dial device',
            'name': 'Prizmatix — Israel',
            'product': 'CombiLED / UHP-F-LED Series',
            'url': 'https://www.prizmatix.com/combiled/combiled.htm',
            'contact': 'sales@prizmatix.com',
            'desc': (
                'CombiLED combines up to 8 LED wavelength modules into a single fiber output with '
                'I²C microcontroller control — identical architecture to the dial device. Wavelengths '
                '280–1100 nm match nearly every dial position. 12-bit power resolution per channel. '
                'Recommended 8-channel PGM/REE config: 280, 365, 405, 450, 530, 617, 660, 850 nm.'
            ),
            'specs': [
                ['Module',     'λ (nm)', 'Max Power', 'Dial'],
                ['UHP-F-280',  '280',    '300 mW',    'Pos 1'],
                ['UHP-F-365',  '365',    '1000 mW',   'Pos 2 ✓'],
                ['UHP-F-405',  '405',    '1500 mW',   'Pos 3 ✓'],
                ['UHP-F-450',  '450',    '2000 mW',   'Pos 4 ✓'],
                ['UHP-F-530',  '530',    '800 mW',    'Pos 7 ✓'],
                ['UHP-F-617',  '617',    '600 mW',    'Pos A ✓'],
                ['UHP-F-660',  '660',    '1000 mW',   'Pos C ✓'],
                ['UHP-F-850',  '850',    '500 mW',    'Pos E ✓'],
            ],
        },
        {
            'rank': '★★★★★  LIKELY ACTUAL DEVICE — Thorlabs M-series LEDs',
            'name': 'Thorlabs — USA',
            'product': 'M-series Mounted LEDs + DC4100 / LEDD1B Drivers',
            'url': 'https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=2692',
            'contact': 'techsupport@thorlabs.com',
            'desc': (
                'Thorlabs M-series mounted LED wavelengths match dial positions 1–F almost exactly. '
                'The reference device is likely a custom controller board driving Thorlabs LEDs. '
                'DC4100 4-channel driver (I²C/USB) or LEDD1B single-channel drivers (1.2 A each). '
                'Full catalog: 265–1700 nm.'
            ),
            'specs': [
                ['Part #',   'λ (nm)', 'Power',   'Dial pos'],
                ['M280LP1',  '280',    '80 mW',   'Pos 1'],
                ['M365LP1',  '365',    '1200 mW', 'Pos 2'],
                ['M405L4',   '405',    '1300 mW', 'Pos 3'],
                ['M470L5',   '470',    '1300 mW', 'Pos 5'],
                ['M530L4',   '530',    '700 mW',  'Pos 7'],
                ['M617L3',   '617',    '700 mW',  'Pos A'],
                ['M660L4',   '660',    '700 mW',  'Pos C'],
                ['M850L3',   '850',    '600 mW',  'Pos E'],
                ['M940L3',   '940',    '500 mW',  'Pos F'],
            ],
        },
        {
            'rank': '★★★★  CLOSE SECOND',
            'name': 'Mightex Systems — Canada',
            'product': 'WFC-BLS Multi-Wavelength LED',
            'url': 'https://www.mightexsystems.com/family_info.php?cPath=24_51',
            'contact': 'info@mightexsystems.com',
            'desc': (
                'Up to 8 LEDs combined in single fiber output, I²C/USB, 280–1100 nm, 12-bit DAC. '
                'Same concept as Prizmatix with slightly fewer catalog options.'
            ),
            'specs': [
                ['Series',   'Channels', 'Range',      'Control'],
                ['WFC-BLS',  '2–8',      '280–1100 nm','I²C/USB'],
                ['SLC-AA',   '1',        '340–1100 nm','RS-232'],
            ],
        },
        {
            'rank': '★★★  HIGH-END 32-CHANNEL',
            'name': 'Gamma Scientific — USA',
            'product': 'SpectralLED RS-7-VIS / RS-7-UV',
            'url': 'https://www.gamma-sci.com/products/spectraledlightsources/',
            'contact': 'sales@gamma-sci.com',
            'desc': (
                '32-channel LED array, 16-bit DAC per channel, SCPI/RS-232. '
                'RS-7-VIS covers 380–1000 nm; RS-7-UV covers 200–400 nm. '
                'Lab reference standard — more channels than the dial device, same philosophy.'
            ),
            'specs': [
                ['Model',    'Channels', 'Range',      'Control', 'DAC'],
                ['RS-7-VIS', '32',       '380–1000 nm','SCPI',    '16-bit'],
                ['RS-7-UV',  '32',       '200–400 nm', 'SCPI',    '16-bit'],
                ['RS-7-IR',  '32',       '700–1700 nm','SCPI',    '16-bit'],
            ],
        },
        {
            'rank': '★★★  DEEP UV GAP FILL — Pt/Os/Ir primary lines',
            'name': 'Crystal IS / SETi (Asahi Kasei)',
            'product': 'Optan Series / UVTOP265 AlGaN UV-C LEDs',
            'url': 'https://www.crystal-is.com/products/optan-series/',
            'contact': 'sales@crystal-is.com',
            'desc': (
                'AlGaN UV-C LEDs for deep UV — the wavelength gap the hex-dial device cannot cover. '
                'UVTOP265 at 265 nm hits Pt primary line exactly. Must supplement dial device with '
                'these for complete Pt/Os/Ir coverage.'
            ),
            'specs': [
                ['Part',        'λ (nm)', 'Power',  'PGM target'],
                ['UVTOP265',    '265',    '1–5 mW', 'Pt primary (265.9 nm)'],
                ['UVTOP255',    '255',    '1–3 mW', 'Ir primary'],
                ['Optan-270',   '270',    '10 mW',  'Pt/Os region'],
                ['Optan-250',   '250',    '5 mW',   'Os/Ir region'],
            ],
        },
        {
            'rank': '★★★  NIR GAP FILL — Nd/Yb/Er pump',
            'name': 'Roithner LaserTechnik — Austria',
            'product': 'ELJ-808 / ELJ-980 NIR Laser Diodes',
            'url': 'https://www.roithner-laser.com/laser_diodes_808.html',
            'contact': 'office@roithner-laser.com',
            'desc': (
                'NIR laser diodes covering 808 nm (Nd³⁺ pump) and 980 nm (Yb³⁺/Er³⁺ pump) gaps '
                'in the hex dial device. ELJ-808-500M is a 500 mW pigtailed diode.'
            ),
            'specs': [
                ['Part',           'λ (nm)', 'Power',  'REE target'],
                ['ELJ-808-500M',   '808',    '500 mW', 'Nd³⁺ pump'],
                ['ELJ-980-100',    '980',    '100 mW', 'Yb³⁺/Er³⁺'],
                ['ELJ-975-200',    '975',    '200 mW', 'Yb³⁺ exact'],
                ['ELJ-730-100',    '730',    '100 mW', 'Nd³⁺ alt'],
            ],
        },
    ]

    for m in led_mfrs:
        S.append(Spacer(1, 6))
        S.append(Paragraph(f"{m['rank']} — {m['name']}", h2))
        S.append(Paragraph(f"Product: {m['product']}", h3))
        S.append(Paragraph(m['desc'], body))
        S.append(Paragraph(lnk(f"Website: {m['url']}", m['url']), url_s))
        if 'contact' in m:
            S.append(Paragraph(f"Contact: {m['contact']}", small))
        if 'specs' in m:
            nc = len(m['specs'][0])
            S.append(Table(m['specs'], colWidths=even_cols(doc, nc), style=BASE_TBL))
        S.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceAfter=4))

    S.append(Spacer(1, 10))
    S.append(Paragraph(
        'All hyperlinks active — tap/click to open. '
        'Cross-referenced: STARE Research Division PDF June 25, 2026.',
        small))

    doc.build(S)
    print(f'PDF written: {OUT}')
    return OUT


if __name__ == '__main__':
    build_gas_discharge_pdf()
    build_led_pdf()
    print('Done — white background, dark text, WCAG AA contrast.')
