from engine import *

KW = ('CREATE', 'TABLE', 'INT', 'VARCHAR(50)', 'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'INSERT', 'INTO', 'VALUES',
      'UPDATE', 'SET', 'WHERE', 'DELETE', 'FROM', 'SELECT', 'AVG(Preis)', 'NOT', 'IN', 'DROP', 'NOT NULL', 'NULL')

def code(y, lines, hl=None, size=23, x=40, w=640):
    return Code(x, y, w, lines, size=size, kw=KW, hl_lines=hl)

SEG = [
    dict(say='SQL ist mehr als SELECT. Tabellen anlegen, Daten ändern und Unterabfragen. Das kommt in der AP2 regelmäßig dran.',
         cap='SQL: Tabellen anlegen, Daten ändern, Unterabfragen.',
         do=title('SQL: DDL, DML\n& Unterabfragen', 'CREATE · INSERT · UPDATE · DELETE', BLUE, 44)),
    dict(say='Mit CREATE TABLE legst du eine Tabelle an. Der Primärschlüssel identifiziert jede Zeile, und der Fremdschlüssel verweist mit REFERENCES auf eine andere Tabelle.',
         cap='CREATE TABLE: PRIMARY KEY und FOREIGN KEY ... REFERENCES',
         do=[('clear',), ('add', 'c', code(220, ['CREATE TABLE Bestellung (', '  BNr   INT PRIMARY KEY,', '  Datum DATE NOT NULL,',
                                                 '  KNr   INT,', '  FOREIGN KEY (KNr)', '    REFERENCES Kunde(KNr)', ');'],
                                                {1: 'orange', 4: 'blue', 5: 'blue'})),
             ('add', 'n', Text(360, 620, 'DDL = Data Definition Language', 24, MUTED, 'bold'))]),
    dict(say='INSERT INTO fügt eine neue Zeile ein. Die Werte stehen in derselben Reihenfolge wie die Spalten, Texte in einfachen Hochkommas.',
         cap='INSERT INTO: Werte in Spaltenreihenfolge, Texte in Hochkommas.',
         do=[('clear',), ('add', 'c', code(230, ['INSERT INTO Kunde (KNr, Name, Ort)', "VALUES (4, 'Dana', 'Köln');"], {1: 'green'})),
             ('add', 't', Table(60, 420, [120, 240, 240], [['KNr', 'Name', 'Ort'], [1, 'Anna', 'Bonn'], [2, 'Ben', 'Essen'], [4, 'Dana', 'Köln']],
                                'blue', hl={3: 'green'}))]),
    dict(say='UPDATE ändert vorhandene Zeilen. Achtung: Ohne WHERE änderst du jede einzelne Zeile der Tabelle.',
         cap='UPDATE ... SET ... WHERE – ohne WHERE trifft es ALLE Zeilen!',
         do=[('clear',), ('add', 'c', code(230, ['UPDATE Artikel', '  SET Preis = Preis * 1.1', "  WHERE Kategorie = 'Kabel';"], {2: 'orange'})),
             ('add', 'w', Box(60, 470, 600, 90, 'red', lines=['ohne WHERE: alle Preise +10 %'], size=26))]),
    dict(say='DELETE FROM löscht Zeilen, ebenfalls mit WHERE. DROP TABLE dagegen löscht die ganze Tabelle samt Struktur.',
         cap='DELETE löscht Zeilen – DROP TABLE löscht die ganze Tabelle.',
         do=[('add', 'c2', code(620, ['DELETE FROM Bestellung', "  WHERE Datum < '2024-01-01';"], {1: 'orange'})),
             ('add', 'd', Text(360, 800, 'DROP TABLE Bestellung;  = Tabelle weg', 24, RED, 'bold'))]),
    dict(say='Jetzt die Unterabfragen. Gesucht sind alle Artikel, die teurer sind als der Durchschnitt. Zuerst läuft die innere Abfrage und liefert einen einzelnen Wert.',
         cap='Unterabfrage: Die innere Abfrage läuft zuerst und liefert einen Wert.',
         do=[('clear',), ('add', 'c', code(220, ['SELECT Bezeichnung, Preis', 'FROM Artikel', 'WHERE Preis > (', '  SELECT AVG(Preis)', '  FROM Artikel', ');'],
                                                {3: 'purple', 4: 'purple'})),
             ('add', 'r', Box(220, 560, 280, 70, 'purple', lines=['Durchschnitt = 20'], size=25)),
             ('add', 'a', Arrow([(360, 520), (360, 556)], color=PURPLE))]),
    dict(say='Die äußere Abfrage vergleicht dann jede Zeile mit diesem Wert. Eine Aggregatfunktion direkt im WHERE wäre übrigens falsch.',
         cap='Dann vergleicht die äußere Abfrage – AVG direkt im WHERE ist falsch!',
         do=[('add', 't', Table(110, 700, [300, 200], [['Bezeichnung', 'Preis'], ['Maus', '12'], ['Monitor', '149'], ['Kabel', '5'], ['Headset', '39']],
                                'blue', rh=42, hl={2: 'green', 4: 'green'}, strike=(1, 3)))]),
    dict(say='Liefert die Unterabfrage mehrere Werte, brauchst du IN. Mit NOT IN findest du zum Beispiel alle Kunden, die noch nie bestellt haben.',
         cap='Mehrere Werte: IN bzw. NOT IN – z. B. Kunden ohne Bestellung.',
         do=[('clear',), ('add', 'c', code(240, ['SELECT Name', 'FROM Kunde', 'WHERE KNr NOT IN (', '  SELECT KNr', '  FROM Bestellung', ');'],
                                                {2: 'orange'})),
             ('add', 'x', Box(60, 560, 600, 90, 'red', lines=['WHERE KNr = (SELECT ...) bei mehreren Werten: Fehler'], size=22))]),
    dict(say='Merke: DDL definiert Strukturen, also CREATE, ALTER und DROP. DML bearbeitet Daten, also SELECT, INSERT, UPDATE und DELETE.',
         cap='DDL: CREATE, ALTER, DROP. DML: SELECT, INSERT, UPDATE, DELETE.',
         do=[('clear',), ('add', 'ddl', Box(60, 260, 600, 170, 'blue', title='DDL – Struktur', lines=['CREATE · ALTER · DROP'], size=26)),
             ('add', 'dml', Box(60, 470, 600, 170, 'green', title='DML – Daten', lines=['SELECT · INSERT · UPDATE · DELETE'], size=26)),
             ('add', 'tip', Text(360, 720, 'immer prüfen: WHERE vergessen?', 26, RED, 'xbold'))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
