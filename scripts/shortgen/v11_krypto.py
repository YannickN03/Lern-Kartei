from engine import *

def key(x, y, c=ORANGE): return Circle(x, y, 14, 'key', c)

SEG = [
    dict(say='Hybride Verschlüsselung: Wie H-T-T-P-S deine Daten schützt. In drei Schritten.',
         cap='Hybride Verschlüsselung – so schützt HTTPS deine Daten.',
         do=title('Hybride\nVerschlüsselung', 'symmetrisch + asymmetrisch', RED, 46)),
    dict(say='Symmetrisch heißt: ein gemeinsamer Schlüssel zum Ver- und Entschlüsseln, zum Beispiel A-E-S. Das ist schnell, aber wie kommt der Schlüssel sicher zum Empfänger?',
         cap='Symmetrisch (AES): ein Schlüssel, schnell – aber Schlüsselaustausch?',
         do=[('clear',), ('add', 'sym', Box(60, 180, 600, 230, 'orange', title='Symmetrisch  (z. B. AES)',
                                            lines=['1 gemeinsamer Schlüssel', '+ sehr schnell', '– Problem: Schlüsselaustausch'], size=25)),
             ('add', 'k1', key(575, 300))]),
    dict(say='Asymmetrisch heißt: ein Schlüsselpaar, zum Beispiel R-S-A. Mit dem öffentlichen Schlüssel verschlüsselt jeder, entschlüsseln kann nur der private. Sicher, aber langsam.',
         cap='Asymmetrisch (RSA): Public verschlüsselt, nur Private entschlüsselt – langsam.',
         do=[('add', 'asy', Box(60, 460, 600, 260, 'blue', title='Asymmetrisch  (z. B. RSA)',
                                lines=['Schlüsselpaar: öffentlich + privat', 'öffentlich: verschlüsseln', 'privat: entschlüsseln', '– langsam'], size=25)),
             ('add', 'k2', key(575, 580, GREEN)), ('add', 'k3', key(575, 640, RED))]),
    dict(say='Hybrid kombiniert beides. Schritt eins: Der Sender erzeugt einen zufälligen Sitzungsschlüssel und verschlüsselt damit die Daten symmetrisch.',
         cap='1. Zufälliger Sitzungsschlüssel verschlüsselt die Daten (AES).',
         do=[('clear',), ('add', 'snd', Text(180, 160, 'Sender', 28, INK, 'xbold')), ('add', 'rcv', Text(540, 160, 'Empfänger', 28, INK, 'xbold')),
             ('add', 'sep', Arrow([(360, 140), (360, 960)], head=None, dashed=True, color=MUTED)),
             ('add', 'd1', Box(70, 220, 220, 70, 'gray', lines=['Daten'], size=24)), ('add', 'sk', key(110, 340)),
             ('add', 'skl', Text(200, 340, 'Sitzungsschl.', 20, ORANGE, 'bold', 'lm')),
             ('add', 'e1', Box(70, 400, 220, 70, 'orange', lines=['Daten (AES)'], size=22))]),
    dict(say='Schritt zwei: Den kleinen Sitzungsschlüssel verschlüsselt er asymmetrisch, mit dem öffentlichen Schlüssel des Empfängers.',
         cap='2. Sitzungsschlüssel mit dem Public Key des Empfängers verschlüsseln.',
         do=[('add', 'pk', key(110, 530, GREEN)), ('add', 'pkl', Text(200, 530, 'Public Key Empf.', 20, GREEN, 'bold', 'lm')),
             ('add', 'e2', Box(70, 590, 220, 70, 'blue', lines=['Schlüssel (RSA)'], size=22))]),
    dict(say='Beides wird verschickt. Schritt drei: Der Empfänger entschlüsselt mit seinem privaten Schlüssel den Sitzungsschlüssel, und damit dann die Daten.',
         cap='3. Empfänger: Private Key, dann Sitzungsschlüssel, dann Daten.',
         do=[('add', 't1', Arrow([(290, 435), (430, 435)])), ('add', 't2', Arrow([(290, 625), (430, 625)])),
             ('add', 'r2', Box(430, 590, 230, 70, 'blue', lines=['Schlüssel (RSA)'], size=22)),
             ('add', 'r1', Box(430, 400, 230, 70, 'orange', lines=['Daten (AES)'], size=22)),
             ('add', 'pr', key(470, 730, RED)), ('add', 'prl', Text(555, 730, 'Private Key', 20, RED, 'bold', 'lm')),
             ('add', 'u1', Arrow([(645, 662), (645, 878)])), ('add', 'r3', key(470, 830)), ('add', 'r3l', Text(555, 830, 'Sitzungsschl.', 20, ORANGE, 'bold', 'lm')),
             ('add', 'r4', Box(430, 880, 230, 70, 'green', lines=['Daten lesbar'], size=24))]),
    dict(say='So bekommst du das Beste aus beiden Welten: sicherer Schlüsselaustausch und schnelle Verschlüsselung großer Datenmengen. Genau so arbeitet T-L-S.',
         cap='Sicherer Schlüsselaustausch + schnelle Verschlüsselung = TLS.',
         do=[('clear',), ('add', 'v', Box(60, 300, 600, 220, 'green', title='Hybrid = das Beste aus beiden',
                                          lines=['asymmetrisch: nur der Schlüssel', 'symmetrisch: die eigentlichen Daten', 'Einsatz: TLS / HTTPS, E-Mail (PGP)'], size=25))]),
    dict(say='Prüfungsfalle: Bei der digitalen Signatur ist es umgekehrt. Der Sender signiert mit seinem privaten Schlüssel, geprüft wird mit dem öffentlichen.',
         cap='Falle: Signatur umgekehrt – mit Private signieren, mit Public prüfen.',
         do=[('add', 'sig', Box(60, 580, 600, 170, 'red', title='Digitale Signatur', lines=['Sender signiert: eigener Private Key', 'Empfänger prüft: Public Key des Senders'], size=24))]),
]

if __name__ == '__main__':
    import sys
    print(render(SEG, sys.argv[1], audio_file=sys.argv[2] if len(sys.argv) > 2 else None))
