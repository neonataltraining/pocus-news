"""Push a reminder to Frank's phone with a ready-to-send email to Commee (early-bird price switch)."""
import urllib.parse, urllib.request

TOPIC = "https://ntfy.sh/pocus27-weekly-d2ea349b"
TO = "stefan@commee.se"
SUBJECT = "Byta till ordinarie pris i Trippus – POCUS 2027"
BODY = """Hej Stefan!

Påminnelse inför söndag: early bird för POCUS 2027 går ut 28 februari. Kan du byta till ordinarie pris i Trippus från 1 mars?

Det gäller båda platsbiljetterna (internationell och svensk): 9 300 kr blir 10 200 kr. Online (2 500 kr) och priset för låg- och medelinkomstländer (4 500 kr) ligger kvar som de är.

Vi glömde båda två förra året, så därför hör jag av mig lite i förväg :)

Tack!
Frank
"""

mailto = "mailto:" + TO + "?" + urllib.parse.urlencode({"subject": SUBJECT, "body": BODY}, quote_via=urllib.parse.quote)
req = urllib.request.Request(TOPIC, data=("Early bird slutar söndag 28 feb. Tryck för att öppna det färdiga mejlet till Stefan på Commee.\n\n" + BODY).encode(),
    headers={"Title": "Mejla Commee: byt till ordinarie pris", "Priority": "high", "Tags": "warning", "Click": mailto})
urllib.request.urlopen(req, timeout=30)
print("sent")
