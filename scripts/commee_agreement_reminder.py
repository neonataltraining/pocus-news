"""Monday 2 Nov 2026: remind Frank to send Stefan (Commee) the updated user agreement."""
import urllib.parse, urllib.request

TOPIC = "https://ntfy.sh/pocus27-weekly-d2ea349b"
TO = "stefan.wengelin@commee.se"
SUBJECT = "Uppdaterat användaravtal POCUS 2027"
BODY = """Hej Stefan!

Hoppas du har haft en bra resa, eller jobbresa :)

Här kommer det uppdaterade användaravtalet för POCUS 2027 i två versioner: en med ändringarna markerade och en ren version utan.

Har du möjlighet att läsa igenom och titta på de föreslagna ändringarna under dagen? Om allt ser okej ut kan du bara kopiera in texten från den rena versionen i Trippus.

Tack!
Frank
"""

mailto = "mailto:" + TO + "?" + urllib.parse.urlencode({"subject": SUBJECT, "body": BODY}, quote_via=urllib.parse.quote)
msg = ("Skicka användaravtalet till Stefan idag. Tryck för att öppna mejlet.\n"
       "Bifoga: POCUS_2027_User_Agreement_marked_changes.pdf och POCUS_2027_User_Agreement.pdf (i Hämtade filer).")
req = urllib.request.Request(TOPIC, data=msg.encode(), headers={
    "Title": "Mejla Commee: användaravtalet", "Priority": "high", "Tags": "memo", "Click": mailto})
urllib.request.urlopen(req, timeout=30)
print("sent")
