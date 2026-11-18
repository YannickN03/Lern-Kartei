from engine import *

def line_scale(hl=None):
    els = [Arrow([(50, 400), (680, 400)], head='filled', width=3)]
    segs = [(60, 230, 'red', 'ungültig', '< 18'), (230, 520, 'green', 'gültig', '18 – 65'), (520, 670, 'red', 'ungültig', '> 65')]
    for a, b, c, t, r in segs:
        col, f = COLORS[c]
        els += [Box(a + 4, 330, b - a - 8, 50, c, lines=[t], size=22, r=6), Text((a + b) / 2, 440, r, 22, col, 'bold')]
    return Group(*els)

SEG = [
    dict(say='Testfälle finden mit Äquivalenzklassen und Grenzwerten. So geht Blackbox-Testen in der AP2.',
         cap='Äquivalenzklassen und Grenzwerte – Black-Box-Tests in der AP2.',
         do=title('Black-Box-Test', 'Äquivalenzklassen & Grenzwerte', ORANGE)),
    dict(say='Beim Blackbox-Test kennst du den Code nicht. Du testest nur gegen die Anforderung: Eingabe rein, Ausgabe prüfen.',
         cap='Black-Box: Code unbekannt – nur Eingabe und erwartete Ausgabe.',
         do=[('clear',), ('add', 'in', Box(40, 360, 170, 80, 'blue', lines=['Eingabe'], size=26)),
             ('add', 'bb', Group(Box(260, 320, 200, 160, 'gray', fill=(60, 62, 66)), Text(360, 400, '?', 64, (240, 237, 224), 'xbold'))),
             ('add', 'out', Box(510, 360, 170, 80, 'green', lines=['Ausgabe'], size=26)),
             ('add', 'a1', Arrow([(210, 400), (258, 400)])), ('add', 'a2', Arrow([(462, 400), (508, 400)])),
             ('add', 'wb', Text(360, 560, 'White-Box: Code bekannt, z. B.\nAnweisungs- und Zweigüberdeckung', 22, MUTED, 'reg'))]),
    dict(say='Beispiel: Ein Online-Shop erlaubt Kunden von achtzehn bis fünfundsechzig Jahren. Welche Werte testest du?',
         cap='Beispiel: Alter von 18 bis 65 ist erlaubt. Was testen?',
         do=[('clear',), ('add', 'req', Box(60, 200, 600, 90, 'purple', lines=['Anforderung: Alter 18 bis 65 erlaubt'], size=25))]),
    dict(say='Äquivalenzklassen teilen alle Eingaben in Gruppen, die sich gleich verhalten. Hier gibt es eine gültige und zwei ungültige Klassen.',
         cap='Äquivalenzklassen: 1 gültige und 2 ungültige Klassen.',
         do=[('add', 'ln', line_scale())]),
    dict(say='Aus jeder Klasse reicht ein Vertreter, zum Beispiel zehn, vierzig und siebzig. Testet einer davon richtig, gilt das für die ganze Klasse.',
         cap='Je Klasse ein Vertreter: 10, 40 und 70.',
         do=[('add', 'r1', Box(95, 480, 100, 56, 'red', lines=['10'], size=26, r=28)),
             ('add', 'r2', Box(325, 480, 100, 56, 'green', lines=['40'], size=26, r=28)),
             ('add', 'r3', Box(545, 480, 100, 56, 'red', lines=['70'], size=26, r=28))]),
    dict(say='Fehler passieren aber gern an den Rändern, zum Beispiel kleiner statt kleiner gleich. Deshalb kommen Grenzwerte dazu.',
         cap='Fehler stecken an den Rändern: < statt <=. Also Grenzwerte!',
         do=[('add', 'code', Code(110, 620, 500, ['wenn alter > 18 dann', '   erlaubt'], hl_lines={0: 'red'})),
             ('add', 'ring', Ring(290, 652, 64, 46))]),
    dict(say='Teste direkt an jeder Grenze und knapp daneben: siebzehn, achtzehn, fünfundsechzig und sechsundsechzig.',
         cap='Grenzwerte: 17, 18, 65 und 66.',
         do=[('rm', 'code', 'ring', 'r1', 'r2', 'r3')] + [('add', f'g{i}', Box(x - 40, 480, 80, 56, c, lines=[v], size=26, r=28))
                                                          for i, (x, v, c) in enumerate([(180, '17', 'red'), (275, '18', 'green'), (465, '65', 'green'), (560, '66', 'red')])]),
    dict(say='In der Prüfung schreibst du das als Testfalltabelle: Eingabe, erwartetes Ergebnis, und welche Klasse oder Grenze geprüft wird.',
         cap='Prüfung: Testfalltabelle mit Eingabe und erwartetem Ergebnis.',
         do=[('clear',), ('add', 'tt', Table(60, 220, [90, 140, 370], [['Nr', 'Alter', 'Erwartet'], [1, 10, 'abgelehnt (< 18)'], [2, 40, 'erlaubt'], [3, 70, 'abgelehnt (> 65)'],
                                                                     [4, 17, 'abgelehnt (Grenze)'], [5, 18, 'erlaubt (Grenze)'], [6, 65, 'erlaubt (Grenze)'], [7, 66, 'abgelehnt (Grenze)']],
                                              'orange', title='TESTFÄLLE', hl={1: 'red', 3: 'red', 4: 'red', 7: 'red', 2: 'green', 5: 'green', 6: 'green'}))]),
    dict(say='Wichtig: Das erwartete Ergebnis legst du vorher aus der Anforderung fest, nicht nachdem du das Programm ausprobiert hast.',
         cap='Erwartetes Ergebnis kommt aus der Anforderung – vorher!',
         do=[('add', 'ring', Ring(475, 243, 400, 62))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
