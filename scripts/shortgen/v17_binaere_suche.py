from engine import *

VALS = [3, 8, 12, 17, 23, 31, 42, 56]

def arr(state=None, y=330, ptr=None):
    """state: {index: farbe}; ptr: {index: label} (L/M/R unter den Zellen)."""
    state = state or {}
    els = []
    cw, x0 = 78, 48
    for i, v in enumerate(VALS):
        c = state.get(i, 'blue')
        els.append(Box(x0 + i * cw, y, cw - 8, 70, c, lines=[str(v)], size=28, r=6))
        els.append(Text(x0 + i * cw + (cw - 8) / 2, y - 22, str(i), 18, MUTED, 'reg'))
    for i, lab in (ptr or {}).items():
        els.append(Text(x0 + i * cw + (cw - 8) / 2, y + 100, lab, 22, INK, 'xbold'))
    return Group(*els)

def step(no, txt, y, c='gray'):
    return Box(60, y, 600, 64, c, lines=[f'{no}.  {txt}'], size=22, align='lm')

GRAY = {0: 'gray', 1: 'gray', 2: 'gray', 3: 'gray'}

SEG = [
    dict(say='Die binäre Suche: In nur wenigen Schritten durch riesige Datenmengen. Ein Klassiker in der AP2.',
         cap='Binäre Suche – in wenigen Schritten durch große Daten.',
         do=title('Binäre Suche', 'Teile und herrsche', BLUE)),
    dict(say='Die wichtigste Voraussetzung zuerst: Das Array muss sortiert sein. Wir suchen hier die Zahl zweiundvierzig.',
         cap='Voraussetzung: Das Array ist sortiert. Gesucht: 42.',
         do=[('clear',), ('add', 'h', Text(360, 200, 'gesucht: 42', 34, INK, 'xbold')),
             ('add', 'a', arr()), ('add', 'srt', Text(360, 470, 'Voraussetzung: aufsteigend sortiert!', 25, RED, 'bold'))]),
    dict(say='Wir merken uns links gleich null und rechts gleich sieben. Die Mitte ist links plus rechts, ganzzahlig geteilt durch zwei, also drei. Dort steht siebzehn.',
         cap='links = 0, rechts = 7, mitte = (0 + 7) DIV 2 = 3 – 17',
         do=[('rm', 'srt'), ('add', 'a', arr({3: 'orange'}, ptr={0: 'L', 3: 'M', 7: 'R'}))]),
    dict(say='Zweiundvierzig ist größer als siebzehn. Die linke Hälfte fällt komplett weg, und links wird mitte plus eins, also vier.',
         cap='42 > 17 – linke Hälfte weg, links = mitte + 1 = 4',
         do=[('add', 'a', arr({0: 'gray', 1: 'gray', 2: 'gray', 3: 'gray'}, ptr={4: 'L', 7: 'R'})),
             ('add', 's1', step(1, 'mitte 3 – 17 < 42 – links = 4', 560))]),
    dict(say='Neue Mitte: vier plus sieben, ganzzahlig durch zwei, ergibt fünf. Dort steht einunddreißig, wieder zu klein. Also links gleich sechs.',
         cap='mitte = (4 + 7) DIV 2 = 5 – 31 < 42 – links = 6',
         do=[('add', 'a', arr({0: 'gray', 1: 'gray', 2: 'gray', 3: 'gray', 4: 'gray', 5: 'gray'}, ptr={6: 'L', 7: 'R'})),
             ('add', 's2', step(2, 'mitte 5 – 31 < 42 – links = 6', 640))]),
    dict(say='Mitte ist jetzt sechs, und dort steht zweiundvierzig. Gefunden, nach nur drei Vergleichen. Eine lineare Suche hätte sieben gebraucht.',
         cap='mitte = 6 – 42 gefunden! Nur 3 Vergleiche statt 7.',
         do=[('add', 'a', arr({**{i: 'gray' for i in range(6)}, 6: 'green'}, ptr={6: 'M'})),
             ('add', 's3', step(3, 'mitte 6 – 42 gefunden!', 720, 'green'))]),
    dict(say='Als Pseudocode: Solange links kleiner gleich rechts ist, berechnest du die Mitte. Ist der Wert gleich, gibst du die Position zurück. Ist er kleiner, suchst du rechts weiter, sonst links. Findest du nichts, gibst du minus eins zurück.',
         cap='Schleife solange links <= rechts – sonst Rückgabe -1.',
         do=[('clear',), ('add', 'c', Code(40, 220, 640, [
             'funktion binSuche(a, x)', '  links = 0', '  rechts = länge(a) - 1', '  solange links <= rechts',
             '    mitte = (links + rechts) DIV 2', '    wenn a[mitte] = x', '      gib mitte zurück',
             '    sonst wenn a[mitte] < x', '      links = mitte + 1', '    sonst', '      rechts = mitte - 1',
             '  gib -1 zurück'], size=23, kw=('funktion', 'solange', 'wenn', 'sonst', 'gib', 'zurück', 'DIV'),
             hl_lines={3: 'orange', 11: 'red'}))]),
    dict(say='Der Aufwand ist logarithmisch, also O von log n. Bei tausend Elementen reichen etwa zehn Vergleiche, bei einer Million etwa zwanzig. Die lineare Suche braucht im schlimmsten Fall n.',
         cap='Aufwand O(log n): 1.000 Elemente – ca. 10 Vergleiche.',
         do=[('clear',), ('add', 't', Table(60, 260, [200, 200, 200], [['n', 'linear', 'binär'], ['8', '8', '3'], ['1.000', '1.000', 'ca. 10'], ['1.000.000', '1.000.000', 'ca. 20']],
                                            'blue', title='MAXIMALE VERGLEICHE', hl={3: 'green'})),
             ('add', 'o', Text(360, 560, 'linear: O(n)     binär: O(log n)', 30, INK, 'xbold'))]),
    dict(say='Die binäre Suche geht auch rekursiv. Die Funktion ruft sich mit der halben Grenze selbst auf. Wichtig ist die Abbruchbedingung: links größer rechts heißt, nicht gefunden.',
         cap='Rekursiv: Abbruchbedingung + Selbstaufruf mit halbem Bereich.',
         do=[('clear',), ('add', 'c', Code(30, 200, 660, [
             'funktion suche(a, x, links, rechts)', '  wenn links > rechts', '    gib -1 zurück',
             '  mitte = (links + rechts) DIV 2', '  wenn a[mitte] = x', '    gib mitte zurück',
             '  wenn a[mitte] < x', '    gib suche(a, x, mitte+1, rechts) zurück',
             '  gib suche(a, x, links, mitte-1) zurück'], size=21, kw=('funktion', 'wenn', 'gib', 'zurück', 'DIV'),
             hl_lines={1: 'red', 2: 'red', 7: 'purple', 8: 'purple'})),
             ('add', 'l1', Text(360, 640, 'rot: Abbruchbedingung   lila: Selbstaufruf', 22, MUTED, 'bold'))]),
    dict(say='Prüfungstipps: Erwähne immer die Voraussetzung sortiert, teile ganzzahlig, und vergiss das plus eins und minus eins nicht. Sonst läuft die Schleife endlos.',
         cap='Tipps: sortiert, DIV, mitte +/- 1 – sonst Endlosschleife!',
         do=[('clear',), ('add', 'tip', Box(60, 300, 600, 300, 'red', title='Prüfungstipps',
                                            lines=['Array muss sortiert sein', 'Mitte ganzzahlig (DIV)', 'links = mitte + 1 / rechts = mitte - 1',
                                                   'Abbruch: links > rechts – -1'], size=25))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
