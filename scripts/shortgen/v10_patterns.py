from engine import *

KW = ('wenn', 'dann', 'gib', 'zurück', 'ende', 'für', 'jeden', 'in')

SEG = [
    dict(say='Zwei Entwurfsmuster, die in der AP2 immer wieder auftauchen: Singleton und Obserwer.',
         cap='Zwei Entwurfsmuster für die AP2: Singleton und Observer.',
         do=title('Design Patterns', 'Singleton & Observer', PURPLE)),
    dict(say='Das Singleton sorgt dafür, dass es von einer Klasse genau ein Objekt gibt. Typisch für Logger oder eine Datenbankverbindung.',
         cap='Singleton: genau EIN Objekt – z. B. Logger oder DB-Verbindung.',
         do=[('clear',), ('add', 'cls', Box(160, 200, 400, 250, 'purple', title='Logger',
                                            sections=[['- instanz: Logger'], ['- Logger()', '+ getInstanz(): Logger', '+ log(text)']],
                                            size=23, underline=('- instanz: Logger', '+ getInstanz(): Logger')))]),
    dict(say='Der Trick: Der Konstruktor ist privat. Von außen kann also niemand mit new ein zweites Objekt erzeugen.',
         cap='Trick 1: privater Konstruktor – kein new von außen.',
         do=[('add', 'r1', Ring(230, 316, 150, 40))]),
    dict(say='Stattdessen gibt es eine statische Methode get Instanz. Statisch erkennst du im Diagramm am Unterstrich.',
         cap='Trick 2: statische getInstanz() – unterstrichen im UML.',
         do=[('rm', 'r1'), ('add', 'r2', Ring(305, 347, 300, 42))]),
    dict(say='Beim ersten Aufruf wird das Objekt erzeugt, danach immer dasselbe zurückgegeben.',
         cap='Erster Aufruf erzeugt das Objekt, danach immer dasselbe.',
         do=[('rm', 'r2'), ('add', 'code', Code(60, 520, 600, ['getInstanz()', '  wenn instanz = null dann', '    instanz = new Logger()', '  ende wenn', '  gib instanz zurück'], kw=KW))]),
    dict(say='Das Obserwer-Muster: Ein Subjekt benachrichtigt automatisch alle angemeldeten Beobachter, sobald sich etwas ändert.',
         cap='Observer: Subjekt benachrichtigt alle angemeldeten Beobachter.',
         do=[('clear',),
             ('add', 'sub', Box(180, 170, 360, 190, 'blue', title='Wetterstation', sections=[['- beobachter: Liste'], ['+ anmelden(o)', '+ abmelden(o)', '+ benachrichtigen()']], size=22)),
             ('add', 'if', Box(230, 470, 260, 110, 'green', title='«interface»\nBeobachter', sections=[['+ aktualisieren()']], size=22, title_size=21)),
             ('add', 'as', Arrow([(360, 360), (360, 468)], head='open', label='0..*', lpos=.6, loff=(28, 0)))]),
    dict(say='Konkrete Beobachter, etwa eine App und ein Display, implementieren die Schnittstelle. Das zeichnest du mit gestrichelter Linie und hohlem Dreieck.',
         cap='Beobachter implementieren das Interface: gestrichelt mit hohlem Dreieck.',
         do=[('add', 'c1', Box(70, 700, 240, 70, 'orange', title='App', size=22)),
             ('add', 'c2', Box(410, 700, 240, 70, 'orange', title='Display', size=22)),
             ('add', 'i1', Arrow([(190, 698), (190, 640), (330, 640), (330, 582)], head='triangle', dashed=True)),
             ('add', 'i2', Arrow([(530, 698), (530, 640), (390, 640), (390, 582)], head='triangle', dashed=True))]),
    dict(say='Benachrichtigen geht einfach die Liste durch und ruft bei jedem Beobachter aktualisieren auf.',
         cap='benachrichtigen() ruft bei jedem Beobachter aktualisieren() auf.',
         do=[('clear',), ('add', 'code', Code(60, 330, 600, ['benachrichtigen()', '  für jeden b in beobachter', '    b.aktualisieren()'], kw=KW))]),
    dict(say='Der Vorteil: lose Kopplung. Die Wetterstation kennt nur die Schnittstelle, neue Beobachter kommen ohne Änderung dazu.',
         cap='Vorteil: lose Kopplung – neue Beobachter ohne Änderung.',
         do=[('add', 'v', Box(60, 560, 600, 160, 'green', title='Merke', lines=['Singleton: genau eine Instanz', 'Observer: 1 Subjekt, n Beobachter'], size=25))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
