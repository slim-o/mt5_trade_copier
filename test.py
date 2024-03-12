from pushover import Pushover

po = Pushover("abkcrum6gvhtukc6y92eqexgrwes1a")
po.user("uu9g36cgw2kvhawuxxn7fb3fe85hib")

msg = po.msg("Hello, World!")

msg.set("title", "Best title ever!!!")

po.send(msg)