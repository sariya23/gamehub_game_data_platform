class SilverRequiredFiledException(Exception):
    pass


class SilverNameRequired(SilverRequiredFiledException):
    pass


class SilverSteamAppIdRequired(SilverRequiredFiledException):
    pass


class SilverReleaseDateRequired(SilverRequiredFiledException):
    pass
