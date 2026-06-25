"""
STARE Research Division — PDF Report Builder
Light background, dark text, high contrast. Run to regenerate all planning PDFs.
"""

from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                 Paragraph, Spacer, Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Polygon
from reportlab.graphics import renderPDF

W, H = letter

# ── Palette (WCAG AA contrast on white) ──────────────────────────────────────
BG        = colors.white
TEXT      = colors.HexColor('#111111')   # near-black
ACCENT    = colors.HexColor('#00695C')   # deep teal
ACCENT2   = colors.HexColor('#1565C0')   # deep blue
LINK      = colors.HexColor('#0D47A1')   # dark blue — readable on white
WARN      = colors.HexColor('#B71C1C')   # deep red
ROW_ALT   = colors.HexColor('#F5F5F5')   # very light grey
HDR_BG    = colors.HexColor('#E0F2F1')   # light teal header row
RULE      = colors.HexColor('#B2DFDB')   # teal rule

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    h1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=18,
                         textColor=ACCENT, spaceAfter=6, leading=22)
    h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13,
                         textColor=ACCENT, spaceAfter=4, leading=17)
    h3 = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=11,
                         textColor=ACCENT2, spaceAfter=3, leading=14)
    body = ParagraphStyle('body', fontName='Helvetica', fontSize=9,
                           textColor=TEXT, spaceAfter=4, leading=13)
    url_s = ParagraphStyle('url', fontName='Helvetica', fontSize=9,
                            textColor=LINK, spaceAfter=4, leading=13)
    small = ParagraphStyle('small', fontName='Helvetica', fontSize=8,
                            textColor=colors.HexColor('#555555'), leading=11)
    caption = ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=8,
                              textColor=colors.HexColor('#444444'), leading=11,
                              spaceAfter=6)
    return h1, h2, h3, body, url_s, small, caption

h1, h2, h3, body, url_s, small, caption = make_styles()

def lnk(txt, url):
    return f'<link href="{url}" color="#0D47A1"><u>{txt}</u></link>'

# ── Canvas decorator: white BG + header/footer ────────────────────────────────
class LightCanvas(pdfcanvas.Canvas):
    def __init__(self, fn, title='STARE Research Division', **kw):
        super().__init__(fn, **kw)
        self._title = title
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for i, state in enumerate(self._saved_pages, 1):
            self.__dict__.update(state)
            self._draw_chrome(i, total)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_num, total):
        self.saveState()
        # White background
        self.setFillColor(BG)
        self.rect(0, 0, W, H, fill=1, stroke=0)
        # Teal header bar
        self.setFillColor(ACCENT)
        self.rect(0, H - 36, W, 36, fill=1, stroke=0)
        self.setFillColor(colors.white)
        self.setFont('Helvetica-Bold', 11)
        self.drawString(0.5*inch, H - 24, self._title)
        self.setFont('Helvetica', 9)
        self.drawRightString(W - 0.5*inch, H - 24, 'STARE Research Division — June 25, 2026')
        # Footer
        self.setFillColor(ACCENT)
        self.rect(0, 0, W, 22, fill=1, stroke=0)
        self.setFillColor(colors.white)
        self.setFont('Helvetica', 8)
        self.drawString(0.5*inch, 7, 'Confidential — Internal Research Use Only')
        self.drawRightString(W - 0.5*inch, 7, f'Page {page_num} of {total}')
        self.restoreState()

def make_doc(path, title):
    doc = BaseDocTemplate(path, pagesize=letter,
                          leftMargin=0.65*inch, rightMargin=0.65*inch,
                          topMargin=0.75*inch, bottomMargin=0.55*inch)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame)])
    # Inject title into canvas
    original_canvasmaker = lambda fn, **kw: LightCanvas(fn, title=title, **kw)
    return doc, original_canvasmaker

def tbl_style(col_widths=None):
    return TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HDR_BG),
        ('TEXTCOLOR',  (0,0), (-1,0), ACCENT),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 9),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,1), (-1,-1), 8),
        ('TEXTCOLOR',  (0,1), (-1,-1), TEXT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG, ROW_ALT]),
        ('GRID',       (0,0), (-1,-1), 0.4, RULE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# REPORT 1 — Gas Discharge Arc Lamp Manufacturers
# ─────────────────────────────────────────────────────────────────────────────

def build_gas_discharge_pdf():
    OUT = '/home/user/Wintermute/planning/GasDischarge-Manufacturer-Reference.pdf'
    TITLE = 'Gas Discharge Arc Lamp Manufacturers — 528nm SPR / PGM-REE Processing'
    doc, cm = make_doc(OUT, TITLE)
    S = []

    S.append(Paragraph(TITLE, h1))
    S.append(Paragraph(
        'Specification: Dielectric breakdown gas discharge apparatus — gaseous medium in dielectric '
        'housing sustaining electrical arc discharge — primary emission 528 nm (green) for Au/Ag SPR '
        'excitation — continuous or pulsed UV-Vis-NIR across PGM and REE absorption bands.',
        body))
    S.append(HRFlowable(width='100%', thickness=1, color=RULE, spaceAfter=8))

    # Technology overview table
    S.append(Paragraph('Technology Overview', h2))
    tech_data = [
        ['Technology', 'Gas Medium', 'Housing', '528nm?', 'UV Coverage', 'NIR Coverage'],
        ['Xe Short Arc',      'Xenon',    'Quartz (SiO₂)',   'Continuum ✓', '< 200 nm',  'to 2500 nm'],
        ['Hg-Xe Arc',        'Hg + Xe',  'Quartz',          '+ 546nm line','185 nm+',   'to 2500 nm'],
        ['Kr Arc',           'Krypton',  'Quartz',          'Continuum ✓', '< 200 nm',  'to 1000 nm'],
        ['LDLS (laser Xe)',  'Xenon',    'Quartz dielectric','Continuum ✓','170 nm',    'to 2100 nm'],
        ['CERMAX',           'Xenon',    'Al₂O₃ ceramic',   'Continuum ✓', '< 250 nm',  'to 1000 nm'],
        ['DBD',              'Xe/Hg/Kr', 'Dielectric glass', 'Narrow band', 'VUV only',  'limited'],
        ['Microwave plasma', 'Sulfur/Xe','Quartz',          '~520 nm pk ✓','visible',   'limited'],
        ['Sulfur plasma',    'S vapor',  'Quartz',          '520 nm peak ✓','430–750 nm','limited'],
    ]
    S.append(Table(tech_data,
                   colWidths=[1.1*inch, 0.85*inch, 1.1*inch, 0.85*inch, 0.85*inch, 0.85*inch],
                   style=tbl_style()))
    S.append(Spacer(1, 10))

    # Manufacturers
    manufacturers = [
        {
            'rank': '★★★★★ BEST MATCH',
            'name': 'Energetiq Technology (Hamamatsu group)',
            'product': 'LDLS EQ-99XFC / EQ-77',
            'url': 'https://www.energetiq.com/ldls-laser-driven-light-source',
            'desc': (
                'Laser-Driven Light Source: a CW laser sustains a Xe plasma inside a sealed quartz '
                'dielectric bulb — electrodeless, no electrode erosion. Delivers 170–2100 nm '
                'continuous output, covering every PGM and REE absorption band. ~10× higher radiance '
                'than conventional Xe arcs. Fiber-coupled output directly to reaction vessel.'
            ),
            'specs': [
                ['Parameter', 'EQ-99XFC', 'EQ-77'],
                ['Spectral range', '170–2100 nm', '200–1100 nm'],
                ['Output power', '> 1 mW/nm @ 400 nm', '> 0.5 mW/nm'],
                ['Stability', '< 0.2% RMS', '< 0.5% RMS'],
                ['Dielectric housing', 'Fused silica (SiO₂)', 'Fused silica'],
                ['Discharge type', 'Laser-sustained Xe plasma', 'Laser-sustained'],
                ['Arc size', '< 100 µm', '< 100 µm'],
                ['Fiber output', 'SMA-905 or custom', 'SMA-905'],
            ],
        },
        {
            'rank': '★★★★★ LITERAL SPEC MATCH',
            'name': 'Excelitas Technologies — CERMAX',
            'product': 'PE300BF / PE75BF / PE150BF',
            'url': 'https://www.excelitas.com/product-category/cermax-xenon-arc-lamps',
            'desc': (
                'CERMAX = Ceramic Maximum — Al₂O₃ ceramic reflector IS the dielectric housing. '
                'Xe arc burns inside a parabolic ceramic cavity, producing collimated UV-Vis-NIR output. '
                'Long life (1000+ hrs), cold-restrike capable. Widely used in photodynamic therapy, '
                'spectroscopy, and photocatalytic research. Available 75W–1600W.'
            ),
            'specs': [
                ['Model', 'Power', 'Life', 'Spectral range', 'Color temp'],
                ['PE75BF',  '75 W',  '500 hr',  '240–2500 nm', '5500 K'],
                ['PE150BF', '150 W', '1000 hr', '240–2500 nm', '5800 K'],
                ['PE300BF', '300 W', '1000 hr', '240–2500 nm', '6000 K'],
                ['PE1000',  '1000 W','500 hr',  '230–2500 nm', '6200 K'],
            ],
        },
        {
            'rank': '★★★★ TOP PICK FOR 528nm',
            'name': 'Sulfur Plasma / Topanga Technologies (Luxim)',
            'product': 'LiFi Sulfur Plasma Lamp',
            'url': 'https://www.topangatech.com',
            'desc': (
                'Sulfur vapor microwave plasma in quartz dielectric bulb. Natural emission peaks at '
                '~520 nm — closest of any discharge lamp to your 528 nm SPR target without bandpass '
                'filtering. 430–750 nm visible band. 1000W microwave drive, electrodeless, 50,000+ hr '
                'life. Heraeus and LumaCept are alternative suppliers of sulfur plasma systems.'
            ),
            'specs': [
                ['Parameter', 'Value'],
                ['Peak emission',   '~520 nm (natural)'],
                ['Spectral range',  '430–750 nm'],
                ['Drive frequency', '2.45 GHz microwave'],
                ['Housing',         'Fused quartz dielectric bulb'],
                ['Lifetime',        '50,000+ hours'],
                ['Input power',     '1000–1400 W'],
            ],
        },
        {
            'rank': '★★★★',
            'name': 'Newport / MKS Instruments — Oriel Series',
            'product': 'Model 66902 / 69911 / 67005 Xe Arc',
            'url': 'https://www.newport.com/c/arc-lamp-sources',
            'desc': (
                'Industry-standard Xe short arc systems. Quartz envelope xenon arc, 150W–1000W, '
                'UV-Vis-NIR continuum 200–2500 nm. Paired with Oriel monochromators or bandpass '
                'filters for wavelength selection. The 66902 (150W) is commonly used in photocatalysis '
                'research exactly matching this PGM/REE processing application.'
            ),
            'specs': [
                ['Model',    'Power',  'Range',       'Use case'],
                ['66902',    '150 W',  '200–2500 nm', 'Photocatalysis, SPR'],
                ['69911',    '300 W',  '200–2500 nm', 'High irradiance'],
                ['67005',    '500 W',  '200–2500 nm', 'Large beam area'],
                ['Hg-Xe 66142', '200 W','185–2500 nm','UV-enhanced + 546nm line'],
            ],
        },
        {
            'rank': '★★★★',
            'name': 'Hamamatsu Photonics',
            'product': 'L10671 / L11035 / LC8 Series',
            'url': 'https://www.hamamatsu.com/us/en/product/light-sources/xenon-flash-lamps.html',
            'desc': (
                'Hamamatsu offers Xe short arc lamps (continuous and flash) plus their Lightningcure '
                'LC8 UV spot light source. The L10671 is a compact fiber-coupled Xe lamp widely used '
                'in optical spectroscopy. Flash Xe lamps (L9455 series) provide pulsed µs–ms pulses '
                'for time-resolved PGM photoluminescence measurements.'
            ),
            'specs': [
                ['Model',    'Type',    'Range',       'Output'],
                ['L10671',   'CW Xe',   '200–2000 nm', '150 W'],
                ['L11035',   'CW Xe',   '200–2000 nm', '75 W compact'],
                ['L9455',    'Flash Xe','200–1000 nm', '0.1–10 ms pulse'],
                ['LC8',      'UV spot', '240–400 nm',  '200 mW/cm²'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'ams OSRAM — XBO Series',
            'product': 'XBO 75W/2 / XBO 150W/4 / XBO 300W',
            'url': 'https://www.ams-osram.com/products/lamps/xenon-short-arc-lamps',
            'desc': (
                'XBO short arc xenon lamps — ultra-high pressure, small arc gap (< 1mm), extremely '
                'high luminance. Used in cinema projectors and scientific instruments requiring small '
                'source size (high etendue). Available with UV-transmitting quartz for deep UV output '
                'down to 230 nm — covers Pt (265 nm), Os, and Ir primary lines.'
            ),
            'specs': [
                ['Model',        'Power',  'Arc gap', 'Color temp'],
                ['XBO 75W/2',    '75 W',   '0.8 mm',  '6200 K'],
                ['XBO 150W/4',   '150 W',  '1.2 mm',  '6200 K'],
                ['XBO 300W/4',   '300 W',  '2.0 mm',  '6000 K'],
                ['XBO 1000W/HS', '1000 W', '5.5 mm',  '6100 K'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Ushio America',
            'product': 'UXL / SX Series Xenon Arc',
            'url': 'https://www.ushio.com/products/arc-lamps/',
            'desc': (
                'Ushio produces high-quality Xe short arc and Hg-Xe lamps. The UXL-75XE is a '
                'workhorse for spectroscopy. Ushio also manufactures specialty Xe lamps with ceramic '
                'holders for harsh environments. Their SX series includes lamps optimized for UV '
                'curing and photocatalytic reactor applications.'
            ),
            'specs': [
                ['Model',    'Power', 'Type',   'Range'],
                ['UXL-75XE', '75 W',  'Xe arc', '230–2500 nm'],
                ['UXL-300D', '300 W', 'Xe arc', '230–2500 nm'],
                ['UXL-500D', '500 W', 'Xe arc', '230–2500 nm'],
                ['SX-UID75XAM','75 W','Xe spot','240–700 nm'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Resonance Ltd',
            'product': 'Microwave-Excited Electrodeless Lamps',
            'url': 'https://www.resonance.on.ca',
            'desc': (
                'Canadian manufacturer specializing in electrodeless microwave-excited discharge lamps '
                'for analytical spectroscopy. Gas-fill selectable: Xe, Kr, Ar, or Hg — each giving '
                'different spectral line patterns. Quartz dielectric bulb, no electrodes (electrodeless '
                'discharge), 2.45 GHz microwave driver. Pulsed or CW modes.'
            ),
            'specs': [
                ['Fill gas', 'Key emission lines'],
                ['Xenon',   '823, 828, 881, 895, 979 nm + continuum'],
                ['Krypton', '758, 760, 769, 811 nm sharp lines'],
                ['Mercury', '185, 254, 365, 405, 436, 546, 578 nm'],
                ['Argon',   '695, 763, 801, 811, 842, 912 nm'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Edinburgh Instruments',
            'product': 'Xe900 / µF920H Xe Flashlamp',
            'url': 'https://www.edinst.com/products/light-sources/',
            'desc': (
                'Edinburgh Instruments produces pulsed Xe flashlamps and steady-state Xe sources for '
                'fluorescence spectroscopy. The µF920H offers sub-microsecond pulses — ideal for '
                'time-resolved luminescence of Eu³⁺, Tb³⁺, Nd³⁺ REE ions during separation monitoring. '
                '200–900 nm range, quartz housing.'
            ),
            'specs': [
                ['Model',   'Type',       'Pulse width', 'Range'],
                ['Xe900',   'CW Xe arc',  'continuous',  '200–900 nm'],
                ['µF920H',  'Flash Xe',   '< 1 µs',      '200–900 nm'],
                ['EPLED',   'Pulsed LED', '< 100 ps',    '265–980 nm'],
            ],
        },
        {
            'rank': '★★',
            'name': 'Heraeus Noblelight',
            'product': 'Xe / Kr / DBD Specialty Lamps',
            'url': 'https://www.heraeus.com/en/hng/products_and_solutions/uv_curing/xenon_flash_lamps.html',
            'desc': (
                'Heraeus manufactures specialty discharge lamps including dielectric barrier discharge '
                '(DBD) excimer lamps emitting at narrow UV bands (172 nm Xe₂*, 222 nm KrCl*, 308 nm '
                'XeCl*). These are true DBD lamps — dielectric on both electrodes, no arc, silent '
                'discharge — useful for Pt/Os/Ir primary UV lines. Also produces broad-spectrum Xe '
                'flash lamps for photocatalytic reactor applications.'
            ),
            'specs': [
                ['Type',       'Wavelength', 'Application'],
                ['Xe₂* excimer','172 nm',    'VUV photolysis, Os/Ir'],
                ['KrCl* excimer','222 nm',   'Ir line region'],
                ['XeCl* excimer','308 nm',   'Rh photocatalysis'],
                ['Xe flash',   '200–2500 nm','Broad photocatalysis'],
            ],
        },
    ]

    for m in manufacturers:
        S.append(Spacer(1, 8))
        S.append(Paragraph(f"{m['rank']} — {m['name']}", h2))
        S.append(Paragraph(f"Product: {m['product']}", h3))
        S.append(Paragraph(m['desc'], body))
        S.append(Paragraph(lnk(f"Website: {m['url']}", m['url']), url_s))
        if 'specs' in m:
            S.append(Table(m['specs'],
                           colWidths=[doc.width / len(m['specs'][0])] * len(m['specs'][0]),
                           style=tbl_style()))
        S.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceAfter=4))

    # Spectral coverage matrix
    S.append(Spacer(1, 10))
    S.append(Paragraph('Spectral Coverage Matrix vs PGM/REE Targets', h2))
    matrix = [
        ['Target', 'λ (nm)', 'Energetiq LDLS', 'CERMAX Xe', 'Sulfur Plasma', 'Hg-Xe Arc', 'DBD Excimer'],
        ['Au SPR',  '520–528', '✓', '✓', '★ Peak here', '✓', '—'],
        ['Ag SPR',  '400–420', '✓', '✓', '—',           '✓', '—'],
        ['Pd',      '340',     '✓', '✓', '—',           '✓', 'XeCl 308nm~'],
        ['Rh',      '343',     '✓', '✓', '—',           '✓', 'XeCl 308nm~'],
        ['Pt',      '265',     '✓', '✓', '—',           '✓', 'KrCl 222~'],
        ['Os',      '226',     '✓', '✓', '—',           '✓', 'Xe₂* 172~'],
        ['Ir',      '224',     '✓', '✓', '—',           '✓', 'Xe₂* 172~'],
        ['Eu³⁺',   '394',     '✓', '✓', '—',           '✓', '—'],
        ['Tb³⁺',   '365',     '✓', '✓', '—',           '✓', '—'],
        ['Er³⁺',   '660',     '✓', '✓', '✓',           '✓', '—'],
        ['Nd³⁺',   '808',     '✓', '✓', '—',           '✓', '—'],
        ['Yb³⁺',   '980',     '✓', '✓', '—',           '✓', '—'],
    ]
    col_w = [0.85*inch, 0.65*inch, 1.05*inch, 0.9*inch, 1.05*inch, 0.8*inch, 0.9*inch]
    S.append(Table(matrix, colWidths=col_w, style=tbl_style()))

    # Purchase path
    S.append(Spacer(1, 10))
    S.append(Paragraph('Priority Purchase Path', h2))
    purchase = [
        ['Goal', 'Product', 'Manufacturer', 'URL', 'Est. Cost'],
        ['Best overall UV-Vis-NIR', 'EQ-99XFC LDLS', 'Energetiq',
         lnk('energetiq.com', 'https://www.energetiq.com'), '$15k–25k'],
        ['528nm natural peak', 'Sulfur plasma lamp', 'Topanga / Luxim',
         lnk('topangatech.com', 'https://www.topangatech.com'), '$3k–8k'],
        ['Budget Xe arc + filter', 'PE150BF CERMAX', 'Excelitas',
         lnk('excelitas.com', 'https://www.excelitas.com/product-category/cermax-xenon-arc-lamps'), '$500–2k'],
        ['Pulsed REE time-resolve', 'µF920H Flashlamp', 'Edinburgh',
         lnk('edinst.com', 'https://www.edinst.com/products/light-sources/'), '$2k–5k'],
        ['Deep UV (Pt/Os/Ir)', 'Xe₂* 172nm DBD', 'Heraeus',
         lnk('heraeus.com', 'https://www.heraeus.com'), '$1k–3k'],
    ]
    S.append(Table(purchase,
                   colWidths=[1.4*inch, 1.2*inch, 0.9*inch, 1.3*inch, 0.85*inch],
                   style=tbl_style()))

    S.append(Spacer(1, 12))
    S.append(Paragraph(
        'Cross-referenced against STARE Research Division PDF '
        '"High-Capacity LED Systems for Metallurgical Photonic Processing" June 25, 2026. '
        'All hyperlinks are active — tap/click to open manufacturer product pages.',
        small))

    doc.build(S, canvasmaker=cm)
    print(f'PDF written: {OUT}')
    return OUT


# ─────────────────────────────────────────────────────────────────────────────
# REPORT 2 — LED Dial-Tuning Manufacturer Reference
# ─────────────────────────────────────────────────────────────────────────────

def build_led_pdf():
    OUT = '/home/user/Wintermute/planning/LED-Manufacturer-Reference.pdf'
    TITLE = 'LED Dial-Tuning Manufacturers — PGM/REE Metallurgical Processing'
    doc, cm = make_doc(OUT, TITLE)
    S = []

    S.append(Paragraph(TITLE, h1))
    S.append(Paragraph(
        'Hex rotary dial device (0–F wavelength, 0–F power 100mW–1.5W) mapped to closest '
        'commercial LED systems for Platinum Group Metal and Rare Earth Element photonic processing.',
        body))
    S.append(HRFlowable(width='100%', thickness=1, color=RULE, spaceAfter=8))

    S.append(Paragraph('Hex Dial Wavelength Decode', h2))
    dial_data = [
        ['Dial', 'Wavelength', 'PGM/REE Target', 'Match Quality'],
        ['0', 'PROG',   'Custom sequence',              '—'],
        ['1', '280 nm', 'Pt secondary, Gd',             'Good'],
        ['2', '367 nm', 'Tb³⁺ (365nm), Sm, Ag photo',  '±2nm Excellent'],
        ['3', '405 nm', 'Ag SPR, Eu³⁺, Pd porphyrin',  'Exact'],
        ['4', '448 nm', 'Ru(bpy)₃²⁺, Ho³⁺',            '±2nm Excellent'],
        ['5', '470 nm', 'Nd adjacent (464nm)',           '±6nm Good'],
        ['6', '505 nm', 'Tb emission verify',            'Good'],
        ['7', '530 nm', 'Au SPR (peak 520nm)',           '±10nm Good'],
        ['8', '568 nm', 'Tb emission (546nm)',           '±22nm Acceptable'],
        ['9', '591 nm', 'Eu emission (594nm)',           '±3nm Excellent'],
        ['A', '617 nm', 'Eu³⁺ emission',                'Exact'],
        ['B', '627 nm', 'Eu/Pr range',                  'Good'],
        ['C', '655 nm', 'Er³⁺ excitation (660nm)',      '±5nm Good'],
        ['D', '740 nm', 'NIR band',                     'Good'],
        ['E', '850 nm', 'NIR broad',                    'Exact'],
        ['F', '940 nm', 'NIR',                          '±40nm Good'],
    ]
    S.append(Table(dial_data,
                   colWidths=[0.4*inch, 0.75*inch, 2.5*inch, 1.4*inch],
                   style=tbl_style()))
    S.append(Spacer(1, 10))

    led_mfrs = [
        {
            'rank': '★★★★★ BEST MATCH — Closest to dial device',
            'name': 'Prizmatix — Israel',
            'product': 'CombiLED / UHP-F-LED Series',
            'url': 'https://www.prizmatix.com/combiled/combiled.htm',
            'contact': 'sales@prizmatix.com',
            'desc': (
                'CombiLED combines up to 8 LED wavelength modules into one fiber output with I²C '
                'microcontroller control — exact architecture of the dial device shown. Available '
                'wavelengths 280–1100 nm match almost every dial position. 12-bit power resolution '
                'per channel. Recommended 8-channel config for PGM/REE: 280, 365, 405, 450, 530, '
                '617, 660, 850 nm.'
            ),
            'specs': [
                ['Module',        'λ (nm)', 'Power', 'Dial match'],
                ['UHP-F-280',     '280',    '300 mW', 'Pos 1'],
                ['UHP-F-365',     '365',    '1000 mW','Pos 2 ✓'],
                ['UHP-F-405',     '405',    '1500 mW','Pos 3 ✓'],
                ['UHP-F-450',     '450',    '2000 mW','Pos 4 ✓'],
                ['UHP-F-530',     '530',    '800 mW', 'Pos 7 ✓'],
                ['UHP-F-617',     '617',    '600 mW', 'Pos A ✓'],
                ['UHP-F-660',     '660',    '1000 mW','Pos C ✓'],
                ['UHP-F-850',     '850',    '500 mW', 'Pos E ✓'],
            ],
        },
        {
            'rank': '★★★★★ LIKELY ACTUAL DEVICE — Thorlabs M-series LEDs',
            'name': 'Thorlabs — USA',
            'product': 'Mounted LEDs (M-series) + DC4100 / LEDD1B drivers',
            'url': 'https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=2692',
            'contact': 'techsupport@thorlabs.com',
            'desc': (
                'Thorlabs M-series mounted LEDs match dial positions 1–F almost exactly. The device '
                'in the reference video is likely a custom controller board driving Thorlabs LEDs. '
                'DC4100 4-channel driver (I²C/USB) or LEDD1B single-channel drivers, up to 1.2A. '
                'Complete catalog wavelength coverage 265–1700 nm.'
            ),
            'specs': [
                ['Part #',    'λ (nm)', 'Power',  'Dial'],
                ['M280LP1',   '280',    '80 mW',  'Pos 1'],
                ['M365LP1',   '365',    '1200 mW','Pos 2'],
                ['M405L4',    '405',    '1300 mW','Pos 3'],
                ['M470L5',    '470',    '1300 mW','Pos 5'],
                ['M530L4',    '530',    '700 mW', 'Pos 7'],
                ['M617L3',    '617',    '700 mW', 'Pos A'],
                ['M660L4',    '660',    '700 mW', 'Pos C'],
                ['M850L3',    '850',    '600 mW', 'Pos E'],
                ['M940L3',    '940',    '500 mW', 'Pos F'],
            ],
        },
        {
            'rank': '★★★★ CLOSE SECOND',
            'name': 'Mightex Systems — Canada',
            'product': 'WFC-BLS Series Multi-Wavelength LED',
            'url': 'https://www.mightexsystems.com/family_info.php?cPath=24_51',
            'contact': 'info@mightexsystems.com',
            'desc': (
                'WFC-BLS: up to 8 LEDs combined in single fiber output, I²C/USB control, '
                '280–1100 nm, 12-bit DAC power control. Slightly fewer catalog options than '
                'Prizmatix but same concept. SLC series is single-channel fiber-coupled LED '
                'for individual wavelengths.'
            ),
            'specs': [
                ['Series', 'Channels', 'Range',      'Control'],
                ['WFC-BLS', '2–8',    '280–1100 nm', 'I²C / USB'],
                ['SLC-AA',  '1',      '340–1100 nm', 'RS232'],
                ['BLS-SA',  '1–4',    '400–700 nm',  'USB'],
            ],
        },
        {
            'rank': '★★★',
            'name': 'Gamma Scientific — USA',
            'product': 'SpectralLED RS-7-VIS / RS-7-UV',
            'url': 'https://www.gamma-sci.com/products/spectraledlightsources/',
            'contact': 'sales@gamma-sci.com',
            'desc': (
                '32-channel LED array, 16-bit DAC control, SCPI/RS-232 interface. Covers 380–1000 nm '
                '(RS-7-VIS) or 200–400 nm (RS-7-UV). More channels than the dial device but same '
                'discrete-wavelength philosophy. High-end lab reference standard.'
            ),
            'specs': [
                ['Model',      'Channels', 'Range',      'Control', 'DAC'],
                ['RS-7-VIS',   '32',       '380–1000 nm','SCPI',    '16-bit'],
                ['RS-7-UV',    '32',       '200–400 nm', 'SCPI',    '16-bit'],
                ['RS-7-IR',    '32',       '700–1700 nm','SCPI',    '16-bit'],
            ],
        },
        {
            'rank': '★★★ DEEP UV GAP FILL — Pt/Os/Ir primary lines',
            'name': 'SETi / Crystal IS (Asahi Kasei)',
            'product': 'UVTOP265 / UVTOP255 AlGaN UV-C LEDs',
            'url': 'https://www.crystal-is.com/products/optan-series/',
            'contact': 'sales@crystal-is.com',
            'desc': (
                'AlGaN UV-C LEDs for deep UV — the wavelength gap the hex-dial device cannot cover. '
                'UVTOP265 at 265 nm hits Pt primary line exactly. UVTOP255 covers Ir. Optan series '
                'from Crystal IS (Asahi Kasei) offers 250–280 nm with fiber-coupled packages. '
                'Must supplement dial device with these for complete Pt/Os/Ir coverage.'
            ),
            'specs': [
                ['Part',        'λ (nm)', 'Power',  'PGM target'],
                ['UVTOP265',    '265',    '1–5 mW', 'Pt primary'],
                ['UVTOP255',    '255',    '1–3 mW', 'Ir primary'],
                ['Optan-270',   '270',    '10 mW',  'Pt/Os region'],
                ['Optan-250',   '250',    '5 mW',   'Os/Ir region'],
            ],
        },
        {
            'rank': '★★★ NIR GAP FILL — Nd/Yb/Er pump',
            'name': 'Roithner LaserTechnik — Austria',
            'product': 'ELJ-808 / ELJ-980 NIR Laser Diodes',
            'url': 'https://www.roithner-laser.com/laser_diodes_808.html',
            'contact': 'office@roithner-laser.com',
            'desc': (
                'Roithner specializes in NIR laser diodes and LEDs that cover the 808 nm (Nd³⁺ pump) '
                'and 980 nm (Yb³⁺/Er³⁺ pump) gaps in the hex dial device. ELJ-808-500M is a '
                '500mW pigtailed diode. Also available: 730nm for Nd³⁺ ground state, 975nm for Yb.'
            ),
            'specs': [
                ['Part',          'λ (nm)', 'Power',   'REE target'],
                ['ELJ-808-500M',  '808',    '500 mW',  'Nd³⁺ pump'],
                ['ELJ-980-100',   '980',    '100 mW',  'Yb³⁺/Er³⁺'],
                ['ELJ-975-200',   '975',    '200 mW',  'Yb³⁺ exact'],
                ['ELJ-730-100',   '730',    '100 mW',  'Nd³⁺ alt'],
            ],
        },
    ]

    for m in led_mfrs:
        S.append(Spacer(1, 8))
        S.append(Paragraph(f"{m['rank']} — {m['name']}", h2))
        S.append(Paragraph(f"Product: {m['product']}", h3))
        S.append(Paragraph(m['desc'], body))
        S.append(Paragraph(lnk(f"Website: {m['url']}", m['url']), url_s))
        if 'contact' in m:
            S.append(Paragraph(f"Contact: {m['contact']}", small))
        if 'specs' in m:
            S.append(Table(m['specs'],
                           colWidths=[doc.width / len(m['specs'][0])] * len(m['specs'][0]),
                           style=tbl_style()))
        S.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceAfter=4))

    S.append(Spacer(1, 12))
    S.append(Paragraph(
        'All hyperlinks are active — tap/click to open manufacturer product pages. '
        'Cross-referenced against STARE Research Division PDF June 25, 2026.',
        small))

    doc.build(S, canvasmaker=cm)
    print(f'PDF written: {OUT}')
    return OUT


if __name__ == '__main__':
    build_gas_discharge_pdf()
    build_led_pdf()
    print('All PDFs generated with high-contrast light theme.')
