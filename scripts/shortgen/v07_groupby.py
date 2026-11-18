from engine import *

KW = ('SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING', 'ORDER', 'AS')

rows = [['Kunde', 'Betrag'], ['Anna', 20], ['Ben', 15], ['Anna', 30], ['Carl', 5], ['Ben', 25]]
grp = {1: 'blue', 3: 'blue', 2: 'green', 5: 'green', 4: 'orange'}

SEG = [
    dict(say='Gruppieren in Es-Ku-El: Group bai und Häwing. Das kommt in fast jeder Prüfung dran.',
         cap='GROUP BY und HAVING – kommt in fast jeder Prüfung dran.',
         do=title('GROUP BY & HAVING', 'Gruppen bilden und filtern')),
    dict(say='Wir starten mit einer Tabelle Bestellung. Jede Zeile hat einen Kunden und einen Betrag.',
         cap='Eine Tabelle Bestellung: Kunde und Betrag.',
         do=[('clear',), ('add', 'tb', Table(170, 200, [200, 180], rows, 'blue', title='BESTELLUNG'))]),
    dict(say='Group bai Kunde fasst alle Zeilen mit demselben Kunden zu einer Gruppe zusammen.',
         cap='GROUP BY Kunde fasst gleiche Kunden zu einer Gruppe zusammen.',
         do=[('add', 'tb', Table(170, 200, [200, 180], rows, 'blue', title='BESTELLUNG', hl=grp)),
             ('add', 'code', Code(50, 560, 620, ['SELECT Kunde, SUM(Betrag)', 'FROM Bestellung', 'GROUP BY Kunde;'], kw=KW))]),
    dict(say='Die Aggregatfunktion Summe rechnet dann pro Gruppe. Aus fünf Zeilen werden drei.',
         cap='SUM rechnet pro Gruppe: aus fünf Zeilen werden drei.',
         do=[('add', 'ar', Arrow([(360, 712), (360, 772)])),
             ('add', 'res', Table(150, 820, [210, 210], [['Kunde', 'SUM(Betrag)'], ['Anna', 50], ['Ben', 40], ['Carl', 5]], 'green', title='ERGEBNIS',
                                   hl={1: 'blue', 2: 'green', 3: 'orange'}))]),
    dict(say='Wichtige Regel: Jede Spalte im Selekt steht entweder im Group bai, oder in einer Aggregatfunktion.',
         cap='Regel: Jede Spalte im SELECT steht im GROUP BY oder in einer Aggregatfunktion.',
         do=[('clear',),
             ('add', 'rule', Box(60, 250, 600, 200, 'purple', title='Die GROUP-BY-Regel',
                                 lines=['Jede Spalte im SELECT steht …', '… im GROUP BY  oder', '… in COUNT, SUM, AVG, MIN, MAX'], size=24)),
             ('add', 'ok', Code(60, 520, 600, ['SELECT Kunde, COUNT(*)', 'GROUP BY Kunde'], kw=KW)),
             ('add', 'okc', Check(620, 572)),
             ('add', 'bad', Code(60, 680, 600, ['SELECT Kunde, Betrag', 'GROUP BY Kunde'], kw=KW)),
             ('add', 'badc', Cross(620, 732))]),
    dict(say='Mit Häwing filterst du ganze Gruppen. Häwing Summe größer dreißig lässt nur Anna und Ben übrig.',
         cap='HAVING filtert Gruppen: SUM > 30 lässt nur Anna und Ben übrig.',
         do=[('clear',),
             ('add', 'code', Code(50, 180, 620, ['SELECT Kunde, SUM(Betrag)', 'FROM Bestellung', 'GROUP BY Kunde', 'HAVING SUM(Betrag) > 30;'], kw=KW,
                                  hl_lines={3: 'orange'})),
             ('add', 'res', Table(150, 500, [210, 210], [['Kunde', 'SUM(Betrag)'], ['Anna', 50], ['Ben', 40], ['Carl', 5]], 'green', title='ERGEBNIS',
                                  strike=(3,)))]),
    dict(say='Merke den Unterschied: Wär filtert einzelne Zeilen, und zwar vor dem Gruppieren. Häwing filtert Gruppen, danach.',
         cap='WHERE filtert Zeilen vorher, HAVING filtert Gruppen danach.',
         do=[('clear',),
             ('add', 'w', Box(50, 330, 300, 270, 'blue', title='WHERE', lines=['filtert Zeilen', 'VOR dem', 'Gruppieren', 'ohne Aggregat'], size=26)),
             ('add', 'h', Box(370, 330, 300, 270, 'orange', title='HAVING', lines=['filtert Gruppen', 'NACH dem', 'Gruppieren', 'mit Aggregat'], size=26))]),
    dict(say='Die Reihenfolge der Ausführung: From, Wär, Group bai, Häwing, Selekt, und zum Schluss Order bai.',
         cap='Ausführung: FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY.',
         do=[('clear',)] + [('add', f'o{i}', Box(200, 170 + i * 120, 320, 70, c, title=t, filled=True, size=26))
                             for i, (t, c) in enumerate([('1  FROM', 'blue'), ('2  WHERE', 'blue'), ('3  GROUP BY', 'purple'),
                                                         ('4  HAVING', 'orange'), ('5  SELECT', 'green'), ('6  ORDER BY', 'gray')])]
             + [('add', f'oa{i}', Arrow([(360, 240 + i * 120), (360, 290 + i * 120)])) for i in range(5)]),
    dict(say='Deshalb ist ein Alias aus dem Selekt im Wär noch gar nicht bekannt.',
         cap='Darum kennt WHERE den Alias aus dem SELECT noch nicht.',
         do=[('add', 'ring', Ring(360, 325, 360, 90))]),
    dict(say='Typischer Prüfungsfehler: eine Aggregatfunktion im Wär. Das ist falsch. Dafür gibt es Häwing.',
         cap='Prüfungsfalle: Aggregat im WHERE ist falsch – dafür gibt es HAVING.',
         do=[('clear',),
             ('add', 'bad', Code(60, 330, 600, ['WHERE SUM(Betrag) > 30'], kw=KW, hl_lines={0: 'red'})),
             ('add', 'x', Cross(620, 372)),
             ('add', 'good', Code(60, 500, 600, ['HAVING SUM(Betrag) > 30'], kw=KW, hl_lines={0: 'green'})),
             ('add', 'v', Check(620, 542))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
