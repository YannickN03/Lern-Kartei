from engine import *

def st(x, y, t, w=210, h=64, c='blue'):
    return Box(x - w / 2, y - h / 2, w, h, c, lines=[t], size=24, r=18)

SEG = [
    dict(say='Das UML Zustandsdiagramm. Es zeigt, in welchen Zuständen ein Objekt sein kann und wodurch es wechselt.',
         cap='Das UML-Zustandsdiagramm: Zustände eines Objekts.',
         do=title('Zustandsdiagramm', 'Zustände & Übergänge', PURPLE)),
    dict(say='Unser Beispiel ist eine Bestellung. Wie beim Aktivitätsdiagramm startet alles mit einem ausgefüllten Kreis, dem Startzustand.',
         cap='Beispiel Bestellung – Start mit dem Startzustand.',
         do=[('clear',), ('add', 'h', Text(360, 150, 'Objekt: Bestellung', 28, INK, 'xbold')),
             ('add', 's0', Circle(360, 220, 16)), ('add', 'a0', Arrow([(360, 236), (360, 290)])),
             ('add', 'z1', st(360, 322, 'Offen'))]),
    dict(say='Zustände zeichnest du als Rechtecke mit abgerundeten Ecken. Ein Zustand beschreibt eine Situation, die eine Weile andauert, etwa offen, bezahlt oder versendet.',
         cap='Zustände: abgerundete Rechtecke – z. B. offen, bezahlt, versendet.',
         do=[('add', 'z2', st(360, 520, 'Bezahlt')), ('add', 'z3', st(360, 720, 'Versendet')), ('add', 'z4', st(615, 322, 'Storniert', 150, c='red'))]),
    dict(say='Die Pfeile sind Transitionen. Die Beschriftung lautet: Ereignis, in eckigen Klammern die Bedingung, und nach dem Schrägstrich die Aktion.',
         cap='Transition: Ereignis [Bedingung] / Aktion',
         do=[('add', 'a1', Arrow([(360, 354), (360, 488)])),
             ('add', 'a1a', Text(345, 405, 'zahlungEingang [betrag ok]', 21, INK, 'reg', 'rm')),
             ('add', 'a1b', Text(345, 437, '/ rechnungSenden()', 21, PURPLE, 'bold', 'rm')),
             ('add', 'syn', Box(60, 900, 600, 70, 'purple', lines=['Ereignis [Bedingung] / Aktion'], size=26))]),
    dict(say='Weitere Übergänge: Wird die Ware verschickt, wechselt die Bestellung in versendet. Ist sie noch offen, kann sie storniert werden.',
         cap='versand: von bezahlt zu versendet – stornieren nur, solange offen.',
         do=[('add', 'a2', Arrow([(360, 552), (360, 688)], label=None)), ('add', 'a2l', Text(345, 620, 'versand', 21, INK, 'reg', 'rm')),
             ('add', 'a3', Arrow([(465, 322), (538, 322)])), ('add', 'a3l', Text(502, 272, 'stornieren', 21, INK, 'reg'))]),
    dict(say='Der Endzustand ist ein Kreis mit Punkt. Davon darf es auch mehrere geben.',
         cap='Endzustand: Kreis mit Punkt – auch mehrere erlaubt.',
         do=[('add', 'a4', Arrow([(360, 752), (360, 820)])), ('add', 'e1', Circle(360, 842, 18, 'end')),
             ('add', 'a5', Arrow([(615, 354), (615, 820)])), ('add', 'e2', Circle(615, 842, 18, 'end')), ('rm', 'syn')]),
    dict(say='In einem Zustand kannst du innere Aktivitäten notieren: entry beim Betreten, do während des Zustands, und exit beim Verlassen.',
         cap='Innere Aktivitäten: entry / do / exit',
         do=[('clear',), ('add', 'big', Box(130, 300, 460, 260, 'blue', title='Versendet',
                                            lines=['entry / trackingNrSpeichern()', 'do / sendungVerfolgen()', 'exit / kundeInformieren()'], size=24, align='lm', r=24))]),
    dict(say='Nicht verwechseln: Das Aktivitätsdiagramm zeigt einen Ablauf von Aktionen. Das Zustandsdiagramm zeigt, wie ein einzelnes Objekt auf Ereignisse reagiert.',
         cap='Aktivität = Ablauf von Aktionen. Zustand = Reaktion eines Objekts auf Ereignisse.',
         do=[('clear',), ('add', 'l', Box(50, 300, 300, 230, 'green', title='Aktivitätsdiagramm', lines=['Ablauf, Aktionen', 'Was passiert?', 'Verb: prüfen'], size=22)),
             ('add', 'r', Box(370, 300, 300, 230, 'purple', title='Zustandsdiagramm', lines=['ein Objekt, Zustände', 'Wie reagiert es?', 'Partizip: bezahlt'], size=22))]),
    dict(say='Prüfungstipps: Zustände benennst du als Adjektiv oder Partizip, jede Transition bekommt ein Ereignis, und Bedingungen immer in eckige Klammern.',
         cap='Tipps: Zustand als Partizip, Ereignis an jeden Pfeil, [Bedingung].',
         do=[('add', 'tip', Box(60, 600, 600, 220, 'red', title='Prüfungstipps',
                                lines=['Zustand: bezahlt, gesperrt, aktiv', 'jeder Pfeil: ein Ereignis', 'Bedingung immer in [ ]'], size=24))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
