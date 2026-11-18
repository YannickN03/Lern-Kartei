from engine import *

def act(x, y, t, w=260, h=62, c='blue'):
    return Box(x - w / 2, y - h / 2, w, h, c, lines=[t], size=23, r=22)

SEG = [
    dict(say='Das U-M-L Aktivitätsdiagramm. Seit dem neuen Prüfungskatalog ein echtes Pflichtthema.',
         cap='Das UML-Aktivitätsdiagramm – seit 2025 ein Pflichtthema.',
         do=title('Aktivitätsdiagramm', 'Abläufe in UML modellieren', GREEN)),
    dict(say='Es zeigt einen Ablauf, also was nacheinander passiert. Jeder Ablauf beginnt mit einem ausgefüllten Kreis, dem Startknoten.',
         cap='Jeder Ablauf beginnt mit dem Startknoten.',
         do=[('clear',), ('add', 'st', Circle(360, 150, 16)), ('add', 'stl', Text(420, 150, 'Startknoten', 20, MUTED, 'reg', 'lm'))]),
    dict(say='Die Schritte heißen Aktionen. Man zeichnet sie als Rechtecke mit stark abgerundeten Ecken.',
         cap='Aktionen: Rechtecke mit abgerundeten Ecken.',
         do=[('rm', 'stl'), ('add', 'a1', Arrow([(360, 166), (360, 214)])), ('add', 'b1', act(360, 246, 'Bestellung prüfen'))]),
    dict(say='Eine Raute ist ein Entscheidungsknoten. An den ausgehenden Kanten stehen Bedingungen in eckigen Klammern, die Wächter.',
         cap='Raute = Entscheidung, Bedingungen in [eckigen Klammern].',
         do=[('add', 'a2', Arrow([(360, 277), (360, 322)])), ('add', 'd1', Diamond(360, 350, 52, 52, 'orange')),
             ('add', 'a3', Arrow([(334, 350), (180, 350), (180, 420)], label='[lieferbar]', lpos=.5, loff=(0, -18))),
             ('add', 'a4', Arrow([(386, 350), (540, 350), (540, 420)], label='[nicht lieferbar]', lpos=.5, loff=(0, -18))),
             ('add', 'b2', act(180, 452, 'Ware verpacken', 230)), ('add', 'b3', act(540, 452, 'Kunde informieren', 230, c='red'))]),
    dict(say='Danach führt ein Verbindungsknoten, wieder eine Raute, die Zweige zusammen.',
         cap='Eine zweite Raute führt die Zweige wieder zusammen.',
         do=[('add', 'a5', Arrow([(180, 483), (180, 560), (334, 560)])), ('add', 'a6', Arrow([(540, 483), (540, 560), (386, 560)])),
             ('add', 'd2', Diamond(360, 560, 52, 52, 'orange'))]),
    dict(say='Parallele Abläufe zeigt ein schwarzer Balken. Die Gabelung teilt den Fluss, die Vereinigung wartet, bis alle Zweige fertig sind.',
         cap='Schwarzer Balken: Gabelung teilt, Vereinigung wartet auf alle.',
         do=[('add', 'a7', Arrow([(360, 586), (360, 630)])), ('add', 'f1', Bar(160, 632, 400)),
             ('add', 'a8', Arrow([(235, 641), (235, 690)])), ('add', 'a9', Arrow([(490, 641), (490, 690)])),
             ('add', 'b4', act(235, 722, 'Rechnung erstellen', 220, c='purple')), ('add', 'b5', act(490, 722, 'Ware versenden', 200, c='purple')),
             ('add', 'a10', Arrow([(235, 753), (235, 800)])), ('add', 'a11', Arrow([(490, 753), (490, 800)])), ('add', 'f2', Bar(160, 802, 400))]),
    dict(say='Am Ende steht der Endknoten: ein Kreis mit Punkt. Er beendet die gesamte Aktivität.',
         cap='Endknoten (Kreis mit Punkt) beendet die ganze Aktivität.',
         do=[('add', 'a12', Arrow([(360, 811), (360, 870)])), ('add', 'en', Circle(360, 892, 18, 'end')),
             ('add', 'enl', Text(395, 892, 'Endknoten', 20, MUTED, 'reg', 'lm'))]),
    dict(say='Nicht verwechseln: Der Kreis mit Kreuz ist ein Ablaufende. Er beendet nur diesen einen Zweig, nicht alles.',
         cap='Kreis mit Kreuz = Ablaufende: beendet nur einen Zweig.',
         do=[('clear',),
             ('add', 'e1', Circle(200, 330, 30, 'end')), ('add', 'e1t', Text(200, 410, 'Endknoten', 26, INK, 'xbold')),
             ('add', 'e1s', Text(200, 450, 'beendet ALLES', 22, MUTED, 'reg')),
             ('add', 'e2', Circle(520, 330, 30, 'flowend')), ('add', 'e2t', Text(520, 410, 'Ablaufende', 26, INK, 'xbold')),
             ('add', 'e2s', Text(520, 450, 'beendet einen Zweig', 22, MUTED, 'reg'))]),
    dict(say='Mit Schwimmbahnen, auch Partitionen genannt, zeigst du, wer welche Aktion ausführt. Zum Beispiel Kunde, Shop und Lager.',
         cap='Schwimmbahnen (Partitionen) zeigen, WER etwas tut.',
         do=[('clear',)] + [('add', f'l{i}', Box(40 + i * 215, 170, 210, 760, c, title=t, size=22, r=4, fill=(244, 241, 231)))
                             for i, (t, c) in enumerate([('Kunde', 'blue'), ('Shop', 'green'), ('Lager', 'orange')])]
             + [('add', 'p0', Circle(145, 270, 14)), ('add', 'pa', Arrow([(145, 284), (145, 330)])), ('add', 'p1', act(145, 362, 'bestellen', 170)),
                ('add', 'pb', Arrow([(230, 362), (275, 362)])), ('add', 'p2', act(360, 362, 'prüfen', 170)),
                ('add', 'pc', Arrow([(360, 393), (360, 470), (500, 470), (500, 520)])), ('add', 'p3', act(575, 552, 'versenden', 170)),
                ('add', 'pd', Arrow([(575, 583), (575, 640)])), ('add', 'p4', Circle(575, 660, 16, 'end'))]),
    dict(say='Prüfungstipps: genau ein Startknoten, Bedingungen immer in eckigen Klammern, und jede Gabelung braucht ihre Vereinigung.',
         cap='Tipp: ein Start, [Bedingungen], jede Gabelung wird vereinigt.',
         do=[('clear',),
             ('add', 'tip', Box(60, 300, 600, 330, 'green', title='Checkliste Prüfung',
                                lines=['genau ein Startknoten', 'Aktionen = Verben („prüfen“)', 'Bedingungen in [eckigen Klammern]',
                                       'Raute: verzweigen und zusammenführen', 'jede Gabelung braucht Vereinigung'], size=25))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
